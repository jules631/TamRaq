from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.settings import settings
from app.tenants.router import router as tenants_router
from app.salesforce.router import router as salesforce_router
from app.sync.router import router as sync_router

# ── Demo mode: pre-seed a tenant so the app works with zero external deps ─────

DEMO_TENANT_ID = "00000000-0000-0000-0000-000000000001"
DEMO_SLUG = "demo-org"

# Minimal RSA-2048 private key used only by the mock Salesforce server path.
# The mock-sf server accepts any token so this key is never actually validated.
_DEMO_PRIVATE_KEY_PEM = """\
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0Z3VS5JJcds3xHn/ygWep4PAtEsHAMKMRZ7bBGhNKMUMbzpn
OGmDxvPQwWi4XPXSDqMOqiirXFRZEHEkfIVgOZHqBnLmqrBrMVWE7kFBVVMDMKOR
bwIpMMByXmIRUoIrBRFMFYqkR8x+ufGWFsREklJjmqDkxO0M8JThCd9YVTG2rTpg
UqNOGFaLFQlFiV0B2bLnBqE2dHlXVCJqrJwuE7/r1dNGEMQ5A8EkLXf+2r6TpZLn
2EKdSrLQdR8VD0E2/ZW1n5r3rHT7E6pq1+J4a9fEEqkBxEn/TBYxBz1kG9zAJpPj
bBD0rZi7rl0EL2wh8HpO7TqU5lhEVA5G3IxIwQIDAQABAoIBAC5RgZ+hBx7xHNaM
pPgwGMnCd2vwhJOri9R9MiCxkQHGMOqaKKTfMFOUMKGQFWVQ9boQ6gxOaGiyoJi8
dCifgPxHCFAUYFJHKNKLDwi5RbNjMF3FhLYLPIQYbX8bCKUwBW7yKZTiRbJUiDAR
5OsxQSmFAqGJmPoaaG6FAbeDgBk2W6HTgVDIuWFVrHQr+VVJKVUFBGHEqIZrJNuS
PzrKXgcAlv/6LKQM3L/Mq+gNm7DmVXjdnIGXqAYqS9Q3eWFRJGYkLuZMSXoBpO2
JT6rXqL0DpGnbkL6RFVgq9aTsVCGQoVFX3L4HE3HI6ayWEeREZFJLKJO5M3X/TGA
6ZkBi4ECgYEA7wgcEvjFr9dBcE1jvqNqVZ8FQ5sBVH/jtVZk0TE5fCFNRcLGYZrR
5fZVmTcJEJg5TqTKEFqYlkPxHFjgK2a5t0F5R0EKVQ8yLFDpQjcJVi7g5i7QR5sX
bZTVEJELG2oXQhR3mF5JrBHzrY8AVJBF4E9NOgmEsV8J3DJvXykCgYEA4HOe0MMq
BSYG4uKRkGMfKOuPmEFgIpXN8w4pMDHZwBt1NJGM3mP5F2LpULRqgMmJHDmf8vkZ
4rPlSz5cqzHnFQAJIORh3qNVbFXdpKq7FplLrYNuFnN3Pz2n3BQ5E5MFAGqOWYMq
mXFzAnDC+8pGCXH3FLJW1jEixUTl3QkCgYEAv8wr0lSqCCLkBj9U+PFfB2hGnlMi
0ZF2RPDSk0VgkPEVsHbpXfXXBkRxfRe6BZEQ9fEVmfAMFXy6A6E4sNGHUuLaSJtY
3hMQE0bLmDBJ4aS3pgjrMCsKE2LwSMGP41dJz3jn9i0HzrPcv1XeKYs9YQSO7HU/
qjsCgYBjBh9MrBr0g8wZFgWW9gPtJE8FbgaZJIL5b9bL3sZEiOkrxH8a4TaO3kQH
MCxPRzWF7K5P+nBZHQj1KZmKqFEUzmxYQLR1MDRXmcyJE3H5N+ZKEb9N8eyrXhNr
5Ow8lBHHBJzX8ELHR3kJqRdJMY3o0gJjuwnPbLO1EUVbEQKBgQCJvTWWHq4F1xmC
XMajG9tIkFNe1k0+sMpTpqHiD7mKlhpuNGU6Z0XB2CYjMj/tD5qJt9oSmUFcE9gP
gGjB2JBe8vQF0kT7s6AQHWIZ/XMYxG3bJMG7nzBaEHkP0OQ9lNJxkQ9C3tP0WPpG
kxHwz8rjFqomDE/0+7yCOHlUbw==
-----END RSA PRIVATE KEY-----
"""


def _seed_demo(db) -> None:
    import uuid
    from app.db.models import Tenant, TenantMember, SalesforceConfig, SyncConfig
    from app.auth.auth0 import DEMO_USER_ID
    from app.utils.crypto import encrypt

    tid = uuid.UUID(DEMO_TENANT_ID)

    tenant = db.get(Tenant, tid)
    if not tenant:
        tenant = Tenant(id=tid, name="Demo Organization", slug=DEMO_SLUG)
        db.add(tenant)
        db.flush()

    member = (
        db.query(TenantMember)
        .filter(TenantMember.tenant_id == tid, TenantMember.auth0_user_id == DEMO_USER_ID)
        .first()
    )
    if not member:
        db.add(TenantMember(tenant_id=tid, auth0_user_id=DEMO_USER_ID))

    sf_cfg = db.query(SalesforceConfig).filter(SalesforceConfig.tenant_id == tid).first()
    if not sf_cfg:
        db.add(SalesforceConfig(
            tenant_id=tid,
            login_url="http://mock-sf:8888",
            client_id="demo-client-id",
            integration_username="demo@example.com",
            encrypted_private_key=encrypt(_DEMO_PRIVATE_KEY_PEM),
        ))

    sync_cfg = db.query(SyncConfig).filter(SyncConfig.tenant_id == tid).first()
    if not sync_cfg:
        db.add(SyncConfig(
            tenant_id=tid,
            household_account_record_type_id=None,
            financial_account_household_lookup_field_api_name="PrimaryOwner__c",
            enable_positions=True,
        ))

    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.DEMO_MODE:
        from app.db.session import SessionLocal
        with SessionLocal() as db:
            _seed_demo(db)
    yield


app = FastAPI(
    title="Tamarac FSC Connector",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tenants_router, prefix="/api")
app.include_router(salesforce_router, prefix="/api")
app.include_router(sync_router, prefix="/api")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}
