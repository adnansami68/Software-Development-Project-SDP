import hashlib
import secrets

QR_PREFIX = "EVTPASS1"


def create_ticket_token() -> str:
    return secrets.token_urlsafe(32)


def hash_ticket_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def make_qr_payload(event_slug: str, token: str) -> str:
    return f"{QR_PREFIX}|{event_slug}|{token}"


def parse_qr_payload(payload: str):
    """Return (event_slug, token) or (None, None) for malformed QR content."""
    if not isinstance(payload, str):
        return None, None
    parts = payload.strip().split("|", 2)
    if len(parts) != 3 or parts[0] != QR_PREFIX or not parts[1] or not parts[2]:
        return None, None
    return parts[1], parts[2]
