import hashlib


def hash_external_id(tenant_salt: str, external_id: str) -> str:
    """
    Return sha256(tenantSalt + externalId) as a hex string.
    Used to identify records in error logs without storing PII.
    """
    raw = (tenant_salt + external_id).encode()
    return hashlib.sha256(raw).hexdigest()
