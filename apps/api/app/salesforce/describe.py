"""
Discovery helpers: Account record types and FinancialAccount link fields.
"""

from app.salesforce.client import SalesforceClient


async def get_account_record_types(sf: SalesforceClient) -> list[dict]:
    result = await sf.query(
        "SELECT Id, Name, DeveloperName FROM RecordType "
        "WHERE SObjectType = 'Account' AND IsActive = true"
    )
    return [
        {"id": r["Id"], "name": r["Name"], "developerName": r["DeveloperName"]}
        for r in result.get("records", [])
    ]


async def get_financial_account_household_link_fields(sf: SalesforceClient) -> list[dict]:
    """
    Describe FinancialAccount and return reference fields that:
    - reference Account (referenceTo includes 'Account')
    - are createable AND updateable
    """
    try:
        desc = await sf.describe("FinancialAccount")
    except Exception:
        # FSC not available in org
        return []

    fields = desc.get("fields", [])
    return [
        {"apiName": f["name"], "label": f["label"]}
        for f in fields
        if f.get("type") == "reference"
        and "Account" in f.get("referenceTo", [])
        and f.get("createable", False)
        and f.get("updateable", False)
    ]
