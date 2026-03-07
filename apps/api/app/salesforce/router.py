from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import require_sf_config, require_tenant_member
from app.db.models import SalesforceConfig
from app.salesforce import describe, schemas
from app.salesforce.client import SalesforceClient

router = APIRouter(tags=["salesforce"])


def _sf_client(cfg: SalesforceConfig) -> SalesforceClient:
    try:
        return SalesforceClient.from_config(cfg)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Salesforce auth failed: {exc}") from exc


@router.post(
    "/tenants/{tenant_id}/salesforce/test",
    response_model=schemas.TestConnectionOut,
)
async def test_connection(
    tenant_id: str,
    cfg: SalesforceConfig = Depends(require_sf_config),
):
    sf = _sf_client(cfg)
    try:
        info = await sf.get_org_info()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Connection test failed: {exc}") from exc
    return schemas.TestConnectionOut(
        orgId=info.get("organization_id", ""),
        instanceUrl=sf.instance_url,
        username=info.get("preferred_username", ""),
    )


@router.get(
    "/tenants/{tenant_id}/salesforce/account-record-types",
    response_model=list[schemas.RecordTypeOut],
)
async def account_record_types(
    tenant_id: str,
    cfg: SalesforceConfig = Depends(require_sf_config),
):
    sf = _sf_client(cfg)
    try:
        return await describe.get_account_record_types(sf)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get(
    "/tenants/{tenant_id}/salesforce/financialaccount-household-link-fields",
    response_model=list[schemas.LinkFieldOut],
)
async def financial_account_link_fields(
    tenant_id: str,
    cfg: SalesforceConfig = Depends(require_sf_config),
):
    sf = _sf_client(cfg)
    try:
        return await describe.get_financial_account_household_link_fields(sf)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
