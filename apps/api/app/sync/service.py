"""
Core sync orchestration: parse CSV → upsert to Salesforce → emit SSE events.

Runs as an asyncio background task. Uses asyncio.to_thread for sync DB writes
to avoid blocking the event loop.
"""

from __future__ import annotations

import asyncio
import csv
import io
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.db.models import SyncConfig, SyncRun
from app.db.session import SessionLocal
from app.salesforce.client import SalesforceClient
from app.sync.sse import remove_run_queue
from app.utils.hashing import hash_external_id
from app.utils.redaction import sanitize_sf_error

logger = logging.getLogger(__name__)

STAGES = [
    "parse_and_validate",
    "upsert_households",
    "upsert_contacts",
    "resolve_ids",
    "upsert_acr",
    "upsert_financial_accounts",
    "upsert_positions",
]


# ── DB helpers (run in thread pool) ──────────────────────────────────────────

def _db_update_run(run_id: str, **kwargs) -> None:
    with SessionLocal() as db:
        run = db.get(SyncRun, uuid.UUID(run_id))
        if run:
            for k, v in kwargs.items():
                setattr(run, k, v)
            db.commit()


async def _update_run(**kwargs) -> None:
    run_id = kwargs.pop("run_id")
    await asyncio.to_thread(_db_update_run, run_id, **kwargs)


# ── Salesforce ID resolution ──────────────────────────────────────────────────

async def _resolve_ids(
    sf: SalesforceClient,
    sobject: str,
    ext_field: str,
    ext_ids: list[str],
) -> dict[str, str]:
    """SOQL IN query to map externalId → Salesforce Id."""
    id_map: dict[str, str] = {}
    for i in range(0, len(ext_ids), 200):
        batch = ext_ids[i : i + 200]
        quoted = ", ".join(f"'{x}'" for x in batch)
        soql = f"SELECT Id, {ext_field} FROM {sobject} WHERE {ext_field} IN ({quoted})"
        result = await sf.query(soql)
        for record in result.get("records", []):
            id_map[record[ext_field]] = record["Id"]
    return id_map


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_float(val: str) -> Optional[float]:
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _is_duplicate_error(result: dict) -> bool:
    for err in result.get("errors", []):
        code = err.get("statusCode", "")
        msg = err.get("message", "").lower()
        if code in ("DUPLICATE_VALUE", "DUPLICATE_DETECTED") or "duplicate" in msg:
            return True
    return False


# ── Main orchestrator ─────────────────────────────────────────────────────────

async def run_sync(
    run_id: str,
    tenant_id: str,
    csv_content: str,
    enable_positions: bool,
    sf: SalesforceClient,
    sync_cfg: SyncConfig,
    queue: asyncio.Queue,
) -> None:
    success_count = 0
    failure_count = 0
    duplicate_count = 0
    sanitized_errors: list[dict] = []
    stage_counts: dict[str, dict] = {}

    async def emit(event: dict) -> None:
        await queue.put(event)

    async def handle_results(
        results: list[dict],
        ext_ids: list[str],
        stage: str,
    ) -> None:
        nonlocal success_count, failure_count, duplicate_count
        for result, ext_id in zip(results, ext_ids):
            if result.get("success"):
                success_count += 1
            elif _is_duplicate_error(result):
                duplicate_count += 1
            else:
                failure_count += 1
                errors = result.get("errors", [])
                raw_msg = errors[0].get("message", "Unknown error") if errors else "Unknown error"
                safe_msg = sanitize_sf_error(raw_msg)
                ext_hash = hash_external_id(tenant_id, ext_id)
                entry = {"stage": stage, "externalIdHash": ext_hash, "message": safe_msg}
                sanitized_errors.append(entry)
                await emit({"type": "error", **entry})

    try:
        # ── Stage 1: parse_and_validate ───────────────────────────────────────
        await emit({"type": "stage", "stage": "parse_and_validate", "status": "started"})

        rows = list(csv.DictReader(io.StringIO(csv_content)))

        households: dict[str, dict] = {}
        contacts: dict[str, dict] = {}
        fin_accounts: dict[str, dict] = {}
        positions: dict[str, dict] = {}
        # ACR key: (hh_ext, contact_ext, role, is_primary)
        acrs: dict[tuple, dict] = {}

        for row in rows:
            hh_id = (row.get("HouseholdExternalId") or "").strip()
            contact_id = (row.get("ContactExternalId") or "").strip()
            fa_id = (row.get("FinancialAccountExternalId") or "").strip()
            pos_id = (row.get("PositionExternalId") or "").strip()
            role = (row.get("ContactRole") or "").strip()
            is_primary = (row.get("IsPrimaryContact") or "").strip()

            if hh_id and hh_id not in households:
                households[hh_id] = row
            if contact_id and contact_id not in contacts:
                contacts[contact_id] = row
            if hh_id and contact_id:
                key = (hh_id, contact_id, role, is_primary)
                if key not in acrs:
                    acrs[key] = row
            if fa_id and fa_id not in fin_accounts:
                fin_accounts[fa_id] = row
            if enable_positions and pos_id and pos_id not in positions:
                positions[pos_id] = row

        counts = {
            "rows": len(rows),
            "households": len(households),
            "contacts": len(contacts),
            "financialAccounts": len(fin_accounts),
            "positions": len(positions),
            "acrs": len(acrs),
        }
        stage_counts["parse_and_validate"] = counts
        await emit({"type": "stage", "stage": "parse_and_validate", "status": "done", **counts})

        # Update DB with total rows
        await _update_run(run_id=run_id, status="running", total_rows=len(rows))

        # ── Stage 2: upsert_households ────────────────────────────────────────
        await emit(
            {"type": "stage", "stage": "upsert_households", "status": "started",
             "total": len(households)}
        )
        hh_records = []
        hh_ext_ids = []
        for ext_id, row in households.items():
            rec = {
                "attributes": {"type": "Account"},
                "TamaracHouseholdId__c": ext_id,
                "Name": (row.get("HouseholdName") or ext_id).strip() or ext_id,
            }
            if sync_cfg and sync_cfg.household_account_record_type_id:
                rec["RecordTypeId"] = sync_cfg.household_account_record_type_id
            hh_records.append(rec)
            hh_ext_ids.append(ext_id)

        if hh_records:
            hh_results = await sf.composite_upsert(
                "Account", "TamaracHouseholdId__c", hh_records
            )
            await handle_results(hh_results, hh_ext_ids, "upsert_households")

        stage_counts["upsert_households"] = {"processed": len(households)}
        await emit(
            {"type": "stage", "stage": "upsert_households", "status": "done",
             "processed": len(households)}
        )

        # ── Stage 3: upsert_contacts ──────────────────────────────────────────
        await emit(
            {"type": "stage", "stage": "upsert_contacts", "status": "started",
             "total": len(contacts)}
        )
        contact_records = []
        contact_ext_ids = []
        for ext_id, row in contacts.items():
            last = (row.get("ContactLastName") or "").strip() or ext_id
            rec = {
                "attributes": {"type": "Contact"},
                "TamaracContactId__c": ext_id,
                "FirstName": (row.get("ContactFirstName") or "").strip(),
                "LastName": last,
            }
            # Only set fields if values present to avoid overwriting with empty strings
            email = (row.get("ContactEmail") or "").strip()
            phone = (row.get("ContactPhone") or "").strip()
            if email:
                rec["Email"] = email
            if phone:
                rec["Phone"] = phone
            contact_records.append(rec)
            contact_ext_ids.append(ext_id)

        if contact_records:
            contact_results = await sf.composite_upsert(
                "Contact", "TamaracContactId__c", contact_records
            )
            await handle_results(contact_results, contact_ext_ids, "upsert_contacts")

        stage_counts["upsert_contacts"] = {"processed": len(contacts)}
        await emit(
            {"type": "stage", "stage": "upsert_contacts", "status": "done",
             "processed": len(contacts)}
        )

        # ── Stage 4: resolve_ids ──────────────────────────────────────────────
        await emit({"type": "stage", "stage": "resolve_ids", "status": "started"})

        hh_id_map: dict[str, str] = {}
        contact_id_map: dict[str, str] = {}

        if households:
            hh_id_map = await _resolve_ids(
                sf, "Account", "TamaracHouseholdId__c", list(households.keys())
            )
        if contacts:
            contact_id_map = await _resolve_ids(
                sf, "Contact", "TamaracContactId__c", list(contacts.keys())
            )

        stage_counts["resolve_ids"] = {
            "householdsResolved": len(hh_id_map),
            "contactsResolved": len(contact_id_map),
        }
        await emit({"type": "stage", "stage": "resolve_ids", "status": "done",
                    **stage_counts["resolve_ids"]})

        # ── Stage 5: upsert_acr ───────────────────────────────────────────────
        await emit(
            {"type": "stage", "stage": "upsert_acr", "status": "started",
             "total": len(acrs)}
        )
        acr_records = []
        acr_keys = []
        for (hh_ext, contact_ext, role, is_primary), _ in acrs.items():
            hh_sf = hh_id_map.get(hh_ext)
            contact_sf = contact_id_map.get(contact_ext)
            if not hh_sf or not contact_sf:
                continue  # Can't create ACR without resolved IDs
            rec: dict = {
                "attributes": {"type": "AccountContactRelation"},
                "AccountId": hh_sf,
                "ContactId": contact_sf,
            }
            if role:
                rec["Roles"] = role
            if is_primary:
                rec["IsDirectRelationship"] = is_primary.lower() in ("true", "yes", "1")
            acr_records.append(rec)
            acr_keys.append(f"{hh_ext}:{contact_ext}")

        if acr_records:
            acr_results = await sf.composite_insert(acr_records)
            await handle_results(acr_results, acr_keys, "upsert_acr")

        stage_counts["upsert_acr"] = {"processed": len(acr_records)}
        await emit(
            {"type": "stage", "stage": "upsert_acr", "status": "done",
             "processed": len(acr_records)}
        )

        # ── Stage 6: upsert_financial_accounts ───────────────────────────────
        await emit(
            {"type": "stage", "stage": "upsert_financial_accounts", "status": "started",
             "total": len(fin_accounts)}
        )
        lookup_field = (
            sync_cfg.financial_account_household_lookup_field_api_name if sync_cfg else None
        )
        fa_records = []
        fa_ext_ids = []
        for ext_id, row in fin_accounts.items():
            hh_ext = (row.get("HouseholdExternalId") or "").strip()
            hh_sf = hh_id_map.get(hh_ext)
            rec: dict = {
                "attributes": {"type": "FinancialAccount"},
                "TamaracAccountId__c": ext_id,
                "Name": (row.get("FinancialAccountName") or ext_id).strip() or ext_id,
            }
            fa_num = (row.get("FinancialAccountNumber") or "").strip()
            custodian = (row.get("Custodian") or "").strip()
            acct_type = (row.get("AccountType") or "").strip()
            if fa_num:
                rec["FinancialAccountNumber"] = fa_num
            if custodian:
                rec["Custodian__c"] = custodian
            if acct_type:
                rec["Type"] = acct_type
            if hh_sf and lookup_field:
                rec[lookup_field] = hh_sf
            fa_records.append(rec)
            fa_ext_ids.append(ext_id)

        if fa_records:
            fa_results = await sf.composite_upsert(
                "FinancialAccount", "TamaracAccountId__c", fa_records
            )
            await handle_results(fa_results, fa_ext_ids, "upsert_financial_accounts")

        stage_counts["upsert_financial_accounts"] = {"processed": len(fa_records)}
        await emit(
            {"type": "stage", "stage": "upsert_financial_accounts", "status": "done",
             "processed": len(fa_records)}
        )

        # ── Stage 7: upsert_positions ─────────────────────────────────────────
        if enable_positions and positions:
            await emit(
                {"type": "stage", "stage": "upsert_positions", "status": "started",
                 "total": len(positions)}
            )
            pos_records = []
            pos_ext_ids = []
            for ext_id, row in positions.items():
                hh_ext = (row.get("HouseholdExternalId") or "").strip()
                hh_sf = hh_id_map.get(hh_ext)
                symbol = (row.get("Symbol") or "").strip()
                rec: dict = {
                    "attributes": {"type": "Asset"},
                    "TamaracPositionId__c": ext_id,
                    "Name": symbol or ext_id,
                    "AccountId": hh_sf or "",
                }
                qty = _safe_float(row.get("Quantity", ""))
                price = _safe_float(row.get("Price", ""))
                mkt_val = _safe_float(row.get("MarketValue", ""))
                cusip = (row.get("CUSIP") or "").strip()
                as_of = (row.get("PositionAsOfDate") or "").strip()
                if qty is not None:
                    rec["Quantity__c"] = qty
                if price is not None:
                    rec["Price"] = price
                if mkt_val is not None:
                    rec["MarketValue__c"] = mkt_val
                if symbol:
                    rec["Symbol__c"] = symbol
                if cusip:
                    rec["CUSIP__c"] = cusip
                if as_of:
                    rec["PositionAsOfDate__c"] = as_of
                pos_records.append(rec)
                pos_ext_ids.append(ext_id)

            if pos_records:
                pos_results = await sf.composite_upsert(
                    "Asset", "TamaracPositionId__c", pos_records
                )
                await handle_results(pos_results, pos_ext_ids, "upsert_positions")

            stage_counts["upsert_positions"] = {"processed": len(pos_records)}
            await emit(
                {"type": "stage", "stage": "upsert_positions", "status": "done",
                 "processed": len(pos_records)}
            )

        # ── Finalize ──────────────────────────────────────────────────────────
        if failure_count == 0:
            final_status = "success"
        elif success_count > 0 or duplicate_count > 0:
            final_status = "partial"
        else:
            final_status = "failed"

        await emit(
            {
                "type": "done",
                "status": final_status,
                "successCount": success_count,
                "failureCount": failure_count,
                "duplicateCount": duplicate_count,
            }
        )
        await _update_run(
            run_id=run_id,
            status=final_status,
            completed_at=datetime.now(timezone.utc),
            success_count=success_count,
            failure_count=failure_count,
            duplicate_count=duplicate_count,
            stage_counts=stage_counts,
            sanitized_errors=sanitized_errors,
        )

    except Exception:
        logger.exception("Sync run %s failed with unhandled exception", run_id)
        await emit({
            "type": "done",
            "status": "failed",
            "message": "Internal sync error",
            "successCount": success_count,
            "failureCount": failure_count,
            "duplicateCount": duplicate_count,
        })
        await _update_run(
            run_id=run_id,
            status="failed",
            completed_at=datetime.now(timezone.utc),
            success_count=success_count,
            failure_count=failure_count,
            duplicate_count=duplicate_count,
            stage_counts=stage_counts,
            sanitized_errors=sanitized_errors,
        )
    finally:
        # Sentinel: SSE generator will close after this
        await queue.put(None)
        # Allow queue to be GC'd shortly after
        asyncio.get_event_loop().call_later(60, remove_run_queue, run_id)
