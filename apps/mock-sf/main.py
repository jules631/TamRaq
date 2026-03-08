"""
Mock Salesforce REST API server for demo/development mode.

Accepts any JWT bearer token and returns plausible success responses.
Does NOT validate credentials — for local demo use only.
"""

import re
import uuid as _uuid

from fastapi import FastAPI, Request

app = FastAPI(title="Mock Salesforce", docs_url="/docs")

INSTANCE_URL = "http://mock-sf:8888"


# ── OAuth ────────────────────────────────────────────────────────────────────

@app.post("/services/oauth2/token")
async def oauth_token():
    return {
        "access_token": "mock-sf-access-token",
        "instance_url": INSTANCE_URL,
        "id": f"{INSTANCE_URL}/id/00D000000000000EAA/005000000000000EAA",
        "token_type": "Bearer",
        "issued_at": "1700000000000",
        "signature": "mock",
    }


# ── Composite upsert (PATCH) ─────────────────────────────────────────────────

@app.patch("/services/data/{version}/composite/sobjects/{sobject}/{ext_field}")
async def composite_upsert(version: str, sobject: str, ext_field: str, request: Request):
    body = await request.json()
    records = body.get("records", [])
    results = [
        {"id": f"001{str(_uuid.uuid4()).replace('-', '')[:15]}", "success": True, "errors": []}
        for _ in records
    ]
    return results


# ── Composite insert (POST) ──────────────────────────────────────────────────

@app.post("/services/data/{version}/composite/sobjects")
async def composite_insert(version: str, request: Request):
    body = await request.json()
    records = body.get("records", [])
    results = [
        {
            "referenceId": r.get("referenceId", str(i)),
            "httpStatusCode": 201,
            "id": f"001{str(_uuid.uuid4()).replace('-', '')[:15]}",
            "success": True,
            "errors": [],
        }
        for i, r in enumerate(records)
    ]
    return {"hasErrors": False, "results": results}


# ── SOQL query ───────────────────────────────────────────────────────────────

def _fake_sf_id(seed: str) -> str:
    """Return a deterministic 18-char SF-style ID from a seed string."""
    hex_seed = _uuid.uuid5(_uuid.NAMESPACE_DNS, seed).hex
    return ("001" + hex_seed)[:18]


def _parse_in_values(soql: str) -> list[str]:
    m = re.search(r"IN\s*\(([^)]+)\)", soql, re.IGNORECASE)
    if not m:
        return []
    raw = m.group(1)
    return [v.strip().strip("'\"") for v in raw.split(",") if v.strip()]


def _detect_ext_field(soql: str) -> str | None:
    m = re.search(r"SELECT\s+Id\s*,\s*(\w+)", soql, re.IGNORECASE)
    return m.group(1) if m else None


@app.get("/services/data/{version}/query")
async def soql_query(version: str, q: str = ""):
    ext_field = _detect_ext_field(q)
    values = _parse_in_values(q)

    if not ext_field or not values:
        return {"totalSize": 0, "done": True, "records": []}

    records = [
        {
            "attributes": {"type": "sObject"},
            "Id": _fake_sf_id(v),
            ext_field: v,
        }
        for v in values
    ]
    return {"totalSize": len(records), "done": True, "records": records}


@app.get("/services/data/{version}/query/")
async def soql_query_trailing(version: str, q: str = ""):
    return await soql_query(version, q)


# ── Describe ─────────────────────────────────────────────────────────────────

@app.get("/services/data/{version}/sobjects/{sobject}/describe")
async def describe(version: str, sobject: str):
    fields = [
        {"name": "Id", "type": "id", "label": "Record ID",
         "createable": False, "updateable": False, "referenceTo": []},
        {"name": "Name", "type": "string", "label": "Name",
         "createable": True, "updateable": True, "referenceTo": []},
    ]
    if sobject == "FinancialAccount":
        fields.append({
            "name": "PrimaryOwner__c",
            "type": "reference",
            "label": "Primary Owner",
            "createable": True,
            "updateable": True,
            "referenceTo": ["Account"],
        })
    return {"name": sobject, "fields": fields}


# ── User info ────────────────────────────────────────────────────────────────

@app.get("/services/oauth2/userinfo")
async def userinfo():
    return {
        "organization_id": "00D000000000001EAA",
        "preferred_username": "demo@example.com",
        "sub": "https://login.salesforce.com/id/00D000000000001EAA/005000000000001EAA",
    }


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "mode": "mock-salesforce"}
