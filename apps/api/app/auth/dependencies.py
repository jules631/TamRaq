import uuid

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.auth0 import verify_token
from app.db.models import SalesforceConfig, SyncConfig, TenantMember
from app.db.session import get_db

bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> dict:
    try:
        payload = verify_token(credentials.credentials)
        return payload
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


async def require_tenant_member(
    tenant_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TenantMember:
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tenant not found")

    user_id: str = current_user["sub"]
    member = (
        db.query(TenantMember)
        .filter(TenantMember.tenant_id == tid, TenantMember.auth0_user_id == user_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this tenant")
    return member


async def require_sf_config(
    tenant_id: str,
    member: TenantMember = Depends(require_tenant_member),
    db: Session = Depends(get_db),
) -> SalesforceConfig:
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tenant not found")

    cfg = db.query(SalesforceConfig).filter(SalesforceConfig.tenant_id == tid).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="Salesforce config not found")
    return cfg


async def require_sync_config(
    tenant_id: str,
    member: TenantMember = Depends(require_tenant_member),
    db: Session = Depends(get_db),
) -> SyncConfig:
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tenant not found")

    cfg = db.query(SyncConfig).filter(SyncConfig.tenant_id == tid).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="Sync config not found")
    return cfg
