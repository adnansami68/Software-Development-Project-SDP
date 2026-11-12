"""Transactional email delivery with a local .eml preview fallback."""

from email.message import EmailMessage
from html import escape
from pathlib import Path
import smtplib
import ssl

from flask import current_app

from .tickets import build_qr_png


def _sender_address() -> str:
    return (
        current_app.config.get("MAIL_DEFAULT_SENDER")
        or current_app.config.get("MAIL_USERNAME")
        or "eventpass@localhost"
    )


def _save_local_preview(message: EmailMessage, filename: str) -> str:
    # Vercel Functions have an ephemeral filesystem. Do not pretend that a
    # preview written there is durable; log a safe message instead.
    if current_app.config.get("IS_VERCEL"):
        current_app.logger.warning("Email preview was not persisted on Vercel; configure a mail provider.")
        return f"Email preview was not saved on hosted storage. Configure SMTP to deliver it to {message['To']}."

    outbox = Path(current_app.instance_path) / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    (outbox / filename).write_bytes(message.as_bytes())
    return f"SMTP is not configured. Email preview saved in instance/outbox/{filename}."


def _deliver_or_save(message: EmailMessage, filename: str):
    cfg = current_app.config
    smtp_ready = bool(cfg.get("MAIL_SERVER") and cfg.get("MAIL_USERNAME") and cfg.get("MAIL_PASSWORD"))

    if cfg.get("MAIL_SUPPRESS_SEND") or not smtp_ready:
        detail = _save_local_preview(message, filename)
        return "preview", detail

    try:
        timeout = int(cfg.get("MAIL_TIMEOUT", 15))
        if cfg.get("MAIL_USE_SSL"):
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(cfg["MAIL_SERVER"], cfg["MAIL_PORT"], context=context, timeout=timeout) as server:
                server.login(cfg["MAIL_USERNAME"], cfg["MAIL_PASSWORD"])
                server.send_message(message)
        else:
            with smtplib.SMTP(cfg["MAIL_SERVER"], cfg["MAIL_PORT"], timeout=timeout) as server:
                server.ehlo()
                if cfg.get("MAIL_USE_TLS", True):
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                server.login(cfg["MAIL_USERNAME"], cfg["MAIL_PASSWORD"])
                server.send_message(message)
        return "sent", f"Ticket email sent to {message['To']}."
    except Exception as exc:  # Email failure must not undo an approved ticket.
        current_app.logger.exception("Ticket email delivery failed")
        preview_message = _save_local_preview(message, filename)
        return "failed", f"Email delivery failed ({type(exc).__name__}). {preview_message}"


def send_registration_received(registration, event):
    msg = EmailMessage()
    msg["Subject"] = f"Registration received — {event.title}"
    msg["From"] = _sender_address()
    msg["To"] = registration.email
    msg.set_content(
        f"Hello {registration.full_name},\n\n"
        f"Your registration for {event.title} has been received and is awaiting organizer approval.\n"
        "Your QR entry ticket will be emailed after approval.\n\n"
        "Thank you.\nEvent Organizer"
    )
    return _deliver_or_save(msg, f"registration-{registration.id}.eml")


def send_approved_ticket(registration, event, pdf_bytes: bytes, token: str):
    msg = EmailMessage()
    msg["Subject"] = f"Your entry ticket — {event.title}"
    msg["From"] = _sender_address()
    msg["To"] = registration.email
    msg.set_content(
        f"Hello {registration.full_name},\n\n"
        f"Your registration for {event.title} has been approved.\n"
        f"Ticket ID: {registration.ticket_code}\n"
        f"Venue: {event.venue}\n"
        f"Event starts: {event.start_at.strftime('%d %B %Y, %I:%M %p')}\n\n"
        "Your PDF entry pass is attached. Present its QR code at the entrance. "
        "Each ticket permits one successful check-in only.\n\nRegards,\nEvent Organizer"
    )

    safe_name = escape(registration.full_name)
    safe_title = escape(event.title)
    safe_venue = escape(event.venue)
    safe_ticket = escape(registration.ticket_code or "")
    qr_png = build_qr_png(event, token)
    html = f"""\
    <html><body style='font-family:Arial,sans-serif;color:#243b53'>
      <h2 style='color:#102a43'>Your event ticket is ready</h2>
      <p>Hello {safe_name},</p>
      <p>Your registration for <strong>{safe_title}</strong> has been approved.</p>
      <p><strong>Ticket ID:</strong> {safe_ticket}<br>
      <strong>Venue:</strong> {safe_venue}<br>
      <strong>Starts:</strong> {event.start_at.strftime('%d %B %Y, %I:%M %p')}</p>
      <p>Your entry QR code is below. A printable PDF pass is also attached.</p>
      <p><img src="cid:ticket-qr" alt="Event entry QR code" width="210" height="210"></p>
      <p style='color:#64748b;font-size:12px'>This ticket allows one successful check-in only. Keep the QR code private.</p>
    </body></html>
    """
    msg.add_alternative(html, subtype="html")
    # EmailMessage.add_alternative() mutates the parent and returns None.
    html_part = msg.get_payload()[-1]
    html_part.add_related(qr_png, maintype="image", subtype="png", cid="<ticket-qr>")

    if pdf_bytes:
        msg.add_attachment(
            pdf_bytes,
            maintype="application",
            subtype="pdf",
            filename=f"{registration.ticket_code or 'event-ticket'}.pdf",
        )
    return _deliver_or_save(msg, f"ticket-{registration.id}.eml")
