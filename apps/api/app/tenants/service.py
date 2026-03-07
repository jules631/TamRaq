import uuid

from sqlalchemy.orm import Session

from app.db.models import SalesforceConfig, SyncConfig, Tenant, TenantMember
from app.utils.crypto import encrypt


def get_or_create_tenant_for_user(db: Session, auth0_user_id: str) -> list[Tenant]:
    """Return the list of tenants the user belongs to; auto-provision one on first login."""
    members = (
        db.query(TenantMember)
        .filter(TenantMember.auth0_user_id == auth0_user_id)
        .all()
    )
    if members:
        tenant_ids = [m.tenant_id for m in members]
        return db.query(Tenant).filter(Tenant.id.in_(tenant_ids)).all()

    # Auto-provision
    safe_slug = auth0_user_id.replace("|", "-")[:50]
    tenant = Tenant(name="My Organization", slug=safe_slug)
    db.add(tenant)
    db.flush()
    member = TenantMember(tenant_id=tenant.id, auth0_user_id=auth0_user_id)
    db.add(member)
    db.commit()
    db.refresh(tenant)
    return [tenant]


def upsert_salesforce_config(
    db: Session,
    tenant_id: uuid.UUID,
    login_url: str,
    client_id: str,
    integration_username: str,
    private_key_pem: str,
) -> SalesforceConfig:
    cfg = db.query(SalesforceConfig).filter(SalesforceConfig.tenant_id == tenant_id).first()
    encrypted = encrypt(private_key_pem)

    if cfg:
        cfg.login_url = login_url
        cfg.client_id = client_id
        cfg.integration_username = integration_username
        cfg.encrypted_private_key = encrypted
    else:
        cfg = SalesforceConfig(
            tenant_id=tenant_id,
            login_url=login_url,
            client_id=client_id,
            integration_username=integration_username,
            encrypted_private_key=encrypted,
        )
        db.add(cfg)

    db.commit()
    db.refresh(cfg)
    return cfg


def upsert_sync_config(
    db: Session,
    tenant_id: uuid.UUID,
    household_account_record_type_id: str | None,
    financial_account_household_lookup_field_api_name: str | None,
    enable_positions: bool,
) -> SyncConfig:
    cfg = db.query(SyncConfig).filter(SyncConfig.tenant_id == tenant_id).first()

    if cfg:
        cfg.household_account_record_type_id = household_account_record_type_id
        cfg.financial_account_household_lookup_field_api_name = (
            financial_account_household_lookup_field_api_name
        )
        cfg.enable_positions = enable_positions
    else:
        cfg = SyncConfig(
            tenant_id=tenant_id,
            household_account_record_type_id=household_account_record_type_id,
            financial_account_household_lookup_field_api_name=financial_account_household_lookup_field_api_name,
            enable_positions=enable_positions,
        )
        db.add(cfg)

    db.commit()
    db.refresh(cfg)
    return cfg
