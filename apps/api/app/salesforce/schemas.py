from pydantic import BaseModel


class TestConnectionOut(BaseModel):
    orgId: str
    instanceUrl: str
    username: str


class RecordTypeOut(BaseModel):
    id: str
    name: str
    developerName: str


class LinkFieldOut(BaseModel):
    apiName: str
    label: str
