"""
Thin async HTTP client wrapper around the Salesforce REST API.
"""

from __future__ import annotations

import httpx

from app.db.models import SalesforceConfig
from app.salesforce.jwt_auth import get_salesforce_token
from app.utils.crypto import decrypt

API_VERSION = "v59.0"
BATCH_SIZE = 200


class SalesforceClient:
    def __init__(self, access_token: str, instance_url: str) -> None:
        self.access_token = access_token
        self.instance_url = instance_url
        self.base_url = f"{instance_url}/services/data/{API_VERSION}"

    @classmethod
    def from_config(cls, cfg: SalesforceConfig) -> "SalesforceClient":
        private_key_pem = decrypt(cfg.encrypted_private_key)
        token_data = get_salesforce_token(
            cfg.login_url,
            cfg.client_id,
            cfg.integration_username,
            private_key_pem,
        )
        return cls(token_data["access_token"], token_data["instance_url"])

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # ── Query ─────────────────────────────────────────────────────────────────

    async def query(self, soql: str) -> dict:
        async with httpx.AsyncClient(timeout=60) as http:
            resp = await http.get(
                f"{self.base_url}/query",
                params={"q": soql},
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def query_all(self, soql: str) -> list[dict]:
        """Handle paginated SOQL results."""
        records: list[dict] = []
        async with httpx.AsyncClient(timeout=60) as http:
            url = f"{self.base_url}/query"
            params: dict = {"q": soql}
            while url:
                resp = await http.get(url, params=params, headers=self._headers())
                resp.raise_for_status()
                data = resp.json()
                records.extend(data.get("records", []))
                next_page = data.get("nextRecordsUrl")
                if next_page and not data.get("done", True):
                    url = f"{self.instance_url}{next_page}"
                    params = {}
                else:
                    url = ""
        return records

    # ── Describe ──────────────────────────────────────────────────────────────

    async def describe(self, sobject: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as http:
            resp = await http.get(
                f"{self.base_url}/sobjects/{sobject}/describe",
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    # ── Composite upsert (PATCH) ───────────────────────────────────────────────

    async def composite_upsert(
        self,
        sobject: str,
        external_id_field: str,
        records: list[dict],
    ) -> list[dict]:
        """Upsert up to BATCH_SIZE records per request, return all results."""
        results: list[dict] = []
        async with httpx.AsyncClient(timeout=120) as http:
            for i in range(0, len(records), BATCH_SIZE):
                batch = records[i : i + BATCH_SIZE]
                resp = await http.patch(
                    f"{self.base_url}/composite/sobjects/{sobject}/{external_id_field}",
                    json={"allOrNone": False, "records": batch},
                    headers=self._headers(),
                )
                resp.raise_for_status()
                results.extend(resp.json())
        return results

    # ── Composite insert (POST) ────────────────────────────────────────────────

    async def composite_insert(self, records: list[dict]) -> list[dict]:
        """Insert records, allOrNone=false. Returns per-record results."""
        results: list[dict] = []
        async with httpx.AsyncClient(timeout=120) as http:
            for i in range(0, len(records), BATCH_SIZE):
                batch = records[i : i + BATCH_SIZE]
                resp = await http.post(
                    f"{self.base_url}/composite/sobjects",
                    json={"allOrNone": False, "records": batch},
                    headers=self._headers(),
                )
                resp.raise_for_status()
                results.extend(resp.json())
        return results

    # ── Org info ──────────────────────────────────────────────────────────────

    async def get_org_info(self) -> dict:
        async with httpx.AsyncClient(timeout=15) as http:
            resp = await http.get(
                f"{self.instance_url}/services/oauth2/userinfo",
                headers={"Authorization": f"Bearer {self.access_token}"},
            )
            resp.raise_for_status()
            return resp.json()
