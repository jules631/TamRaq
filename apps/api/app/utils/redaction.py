import re

# Patterns that look like PII
_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_RE = re.compile(r"\+?[\d][\d\s\-().]{6,}\d")
_NAME_FIELD_RE = re.compile(
    r"(first|last|full|contact|account|household)\s*name[:\s]+\S+", re.IGNORECASE
)


def sanitize_sf_error(message: str) -> str:
    """
    Remove recognizable PII from a Salesforce error message before storing or emitting.
    Keeps the error code / structure intact for debugging.
    """
    msg = _EMAIL_RE.sub("[email]", message)
    msg = _PHONE_RE.sub("[phone]", msg)
    msg = _NAME_FIELD_RE.sub(r"\1 name: [redacted]", msg)
    # Truncate to avoid storing huge payloads
    return msg[:500]
