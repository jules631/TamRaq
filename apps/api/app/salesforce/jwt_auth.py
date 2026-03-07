"""
Salesforce Connected App JWT bearer flow (OAuth 2.0).
https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm
"""

import time

import httpx
import jwt as pyjwt
from cryptography.hazmat.primitives.serialization import load_pem_private_key


def get_salesforce_token(
    login_url: str,
    client_id: str,
    username: str,
    private_key_pem: str,
) -> dict:
    """
    Exchange a signed JWT assertion for a Salesforce access token.
    Returns the full token response dict with access_token, instance_url, etc.
    """
    private_key = load_pem_private_key(private_key_pem.encode(), password=None)

    now = int(time.time())
    claim = {
        "iss": client_id,
        "sub": username,
        "aud": login_url,
        "exp": now + 180,  # Salesforce max is 3 minutes
    }
    assertion = pyjwt.encode(claim, private_key, algorithm="RS256")

    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{login_url}/services/oauth2/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": assertion,
            },
        )
        if not resp.is_success:
            body = resp.text
            raise RuntimeError(f"Salesforce token error {resp.status_code}: {body[:300]}")
        return resp.json()
