from functools import lru_cache

import jwt
from jwt import PyJWKClient

from app.settings import settings


@lru_cache(maxsize=1)
def _get_jwks_client() -> PyJWKClient:
    return PyJWKClient(
        f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json",
        cache_keys=True,
    )


def verify_token(token: str) -> dict:
    client = _get_jwks_client()
    signing_key = client.get_signing_key_from_jwt(token)
    payload: dict = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=settings.AUTH0_AUDIENCE,
        issuer=f"https://{settings.AUTH0_DOMAIN}/",
    )
    return payload
