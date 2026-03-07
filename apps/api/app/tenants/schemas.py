import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TenantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime


class SalesforceConfigIn(BaseModel):
    loginUrl: str
    clientId: str
    integrationUsername: str
    privateKeyPem: str


class SalesforceConfigOut(BaseModel):
    loginUrl: str
    clientId: str
    integrationUsername: str
    # private key is never returned


class SyncConfigIn(BaseModel):
    householdAccountRecordTypeId: str | None = None
    financialAccountHouseholdLookupFieldApiName: str | None = None
    enablePositions: bool = True


class SyncConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    householdAccountRecordTypeId: str | None
    financialAccountHouseholdLookupFieldApiName: str | None
    enablePositions: bool
