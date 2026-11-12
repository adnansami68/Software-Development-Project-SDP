from sqlalchemy import update

from ..extensions import db
from ..models import CheckInLog, Registration, local_now
from .security import hash_ticket_token, parse_qr_payload


def _log(event, result, message, gate, operator_id, ip, registration=None, ticket_code=None):
    entry = CheckInLog(
        event_id=event.id,
        registration_id=registration.id if registration else None,
        ticket_code=ticket_code or (registration.ticket_code if registration else None),
        gate=(gate or "Main Gate")[:80],
        result=result,
        message=message[:255],
        scanned_by=operator_id,
        source_ip=(ip or "")[:64] or None,
    )
    db.session.add(entry)
    db.session.commit()
    return entry


def process_checkin(event, qr_payload, gate, operator_id, ip):
    """Validate a ticket and atomically mark it checked-in exactly once."""
    if event.status != "published" or not event.checkin_open:
        _log(event, "closed", "Check-in is not open for this event.", gate, operator_id, ip)
        return {"ok": False, "status": "closed", "message": "Check-in is currently closed for this event."}

    qr_slug, token = parse_qr_payload(qr_payload)
    if not token or qr_slug != event.slug:
        _log(event, "invalid", "QR code format or event does not match.", gate, operator_id, ip)
        return {"ok": False, "status": "invalid", "message": "Invalid ticket or ticket belongs to another event."}

    token_hash = hash_ticket_token(token)
    registration = Registration.query.filter_by(event_id=event.id, token_hash=token_hash).first()
    if registration is None:
        _log(event, "invalid", "Ticket token was not found.", gate, operator_id, ip)
        return {"ok": False, "status": "invalid", "message": "Ticket not found. Entry denied."}

    if registration.status != "approved":
        _log(event, "invalid", "Ticket is not approved.", gate, operator_id, ip, registration)
        return {"ok": False, "status": "invalid", "message": "This ticket is not approved."}

    scanned_at = local_now()
    result = db.session.execute(
        update(Registration)
        .where(
            Registration.id == registration.id,
            Registration.event_id == event.id,
            Registration.status == "approved",
            Registration.checked_in_at.is_(None),
        )
        .values(checked_in_at=scanned_at, checkin_gate=(gate or "Main Gate")[:80], checked_in_by=operator_id)
    )

    if result.rowcount == 1:
        db.session.expire(registration)
        _log(event, "valid", "Entry approved. Check-in recorded.", gate, operator_id, ip, registration)
        return {
            "ok": True,
            "status": "valid",
            "message": "Entry approved. Check-in successful.",
            "participant": registration.full_name,
            "ticket_code": registration.ticket_code,
            "category": registration.category,
            "checked_in_at": scanned_at.strftime("%d %b %Y, %I:%M:%S %p"),
        }

    db.session.expire(registration)
    registration = db.session.get(Registration, registration.id)
    if registration and registration.checked_in_at:
        _log(event, "duplicate", "Ticket has already been used.", gate, operator_id, ip, registration)
        return {
            "ok": False,
            "status": "duplicate",
            "message": "This ticket has already been used. Duplicate entry blocked.",
            "participant": registration.full_name,
            "ticket_code": registration.ticket_code,
            "checked_in_at": registration.checked_in_at.strftime("%d %b %Y, %I:%M:%S %p"),
        }

    _log(event, "invalid", "Ticket could not be checked in.", gate, operator_id, ip, registration)
    return {"ok": False, "status": "invalid", "message": "Ticket could not be validated."}
