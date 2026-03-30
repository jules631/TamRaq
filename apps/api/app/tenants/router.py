import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_tenant_member
from app.db.models import SalesforceConfig, SyncConfig
from app.db.session import get_db
from app.tenants import schemas, service

router = APIRouter(tags=["tenants"])


# ── Me / tenant discovery ─────────────────────────────────────────────────────

@router.get("/me/tenants", response_model=list[schemas.TenantOut])
def my_tenants(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.get_or_create_tenant_for_user(db, current_user["sub"])


# ── Salesforce config ─────────────────────────────────────────────────────────

@router.put("/tenants/{tenant_id}/config/salesforce")
def put_salesforce_config(
    tenant_id: str,
    body: schemas.SalesforceConfigIn,
    member=Depends(require_tenant_member),
    db: Session = Depends(get_db),
):
    tid = uuid.UUID(tenant_id)
    service.upsert_salesforce_config(
        db,
        tid,
        body.loginUrl,
        body.clientId,
        body.integrationUsername,
        body.privateKeyPem,
    )
    return {"status": "saved"}


@router.get("/tenants/{tenant_id}/config/salesforce", response_model=schemas.SalesforceConfigOut)
def get_salesforce_config(
    tenant_id: str,
    member=Depends(require_tenant_member),
    db: Session = Depends(get_db),
):
    tid = uuid.UUID(tenant_id)
    cfg = db.query(SalesforceConfig).filter(SalesforceConfig.tenant_id == tid).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="Salesforce config not found")
    return schemas.SalesforceConfigOut(
        loginUrl=cfg.login_url,
        clientId=cfg.client_id,
        integrationUsername=cfg.integration_username,
    )


# ── Sync config ───────────────────────────────────────────────────────────────

@router.put("/tenants/{tenant_id}/config/sync")
def put_sync_config(
    tenant_id: str,
    body: schemas.SyncConfigIn,
    member=Depends(require_tenant_member),
    db: Session = Depends(get_db),
):
    tid = uuid.UUID(tenant_id)
    service.upsert_sync_config(
        db,
        tid,
        body.householdAccountRecordTypeId,
        body.financialAccountHouseholdLookupFieldApiName,
        body.enablePositions,
    )
    return {"status": "saved"}


@router.get("/tenants/{tenant_id}/config/sync", response_model=schemas.SyncConfigOut)
def get_sync_config(
    tenant_id: str,
    member=Depends(require_tenant_member),
    db: Session = Depends(get_db),
):
    tid = uuid.UUID(tenant_id)
    cfg = db.query(SyncConfig).filter(SyncConfig.tenant_id == tid).first()
    if not cfg:
        # Return defaults
        return schemas.SyncConfigOut(
            householdAccountRecordTypeId=None,
            financialAccountHouseholdLookupFieldApiName=None,
            enablePositions=True,
        )
    return schemas.SyncConfigOut(
        householdAccountRecordTypeId=cfg.household_account_record_type_id,
        financialAccountHouseholdLookupFieldApiName=cfg.financial_account_household_lookup_field_api_name,
        enablePositions=cfg.enable_positions,
    )
