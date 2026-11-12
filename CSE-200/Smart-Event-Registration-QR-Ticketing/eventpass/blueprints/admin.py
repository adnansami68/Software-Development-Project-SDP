import csv
import io
import re
import secrets
from datetime import datetime
from io import BytesIO
from pathlib import Path

from flask import Blueprint, abort, current_app, flash, jsonify, make_response, redirect, render_template, request, send_file, send_from_directory, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import CheckInLog, Event, Registration, User, local_now
from ..services.attendance import process_checkin
from ..services.mailer import send_approved_ticket
from ..services.security import create_ticket_token, hash_ticket_token
from ..services.tickets import generate_ticket_pdf


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _parse_local_datetime(value: str):
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except (TypeError, ValueError):
        return None


def _slugify(text: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48] or "event"
    return f"{base}-{secrets.token_hex(3)}"


def _ticket_email(registration, event, token):
    """Persist a new one-time ticket before attempting external email delivery."""
    if not registration.ticket_code:
        registration.ticket_code = f"EVT-{event.start_at.year}-{registration.id:06d}"
    registration.token_hash = hash_ticket_token(token)
    pdf_bytes = generate_ticket_pdf(registration, event, token)
    registration.ticket_pdf = f"{registration.ticket_code}.pdf"
    registration.ticket_pdf_data = pdf_bytes
    db.session.commit()
    return send_approved_ticket(registration, event, pdf_bytes, token)


@admin_bp.get("/")
@login_required
def dashboard():
    events = Event.query.order_by(Event.created_at.desc()).limit(6).all()
    total_events = Event.query.count()
    total_registrations = Registration.query.count()
    total_checked_in = Registration.query.filter(Registration.checked_in_at.isnot(None)).count()
    pending = Registration.query.filter_by(status="pending").count()
    recent_logs = CheckInLog.query.order_by(CheckInLog.scanned_at.desc()).limit(8).all()
    return render_template(
        "admin/dashboard.html",
        events=events,
        total_events=total_events,
        total_registrations=total_registrations,
        total_checked_in=total_checked_in,
        pending=pending,
        recent_logs=recent_logs,
    )


@admin_bp.get("/events")
@login_required
def event_list():
    events = Event.query.order_by(Event.created_at.desc()).all()
    return render_template("admin/events.html", events=events)


@admin_bp.route("/events/new", methods=["GET", "POST"])
@login_required
def create_event():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        venue = request.form.get("venue", "").strip()
        start_at = _parse_local_datetime(request.form.get("start_at"))
        end_at = _parse_local_datetime(request.form.get("end_at"))
        deadline = _parse_local_datetime(request.form.get("registration_deadline"))
        capacity_raw = request.form.get("capacity", "").strip()
        capacity = None
        errors = []
        if len(title) < 3:
            errors.append("Event title must contain at least 3 characters.")
        if not venue:
            errors.append("Venue is required.")
        if not start_at or not end_at or not deadline:
            errors.append("Please provide valid start, end and registration deadline values.")
        elif end_at <= start_at:
            errors.append("Event end time must be later than start time.")
        elif deadline > start_at:
            errors.append("Registration deadline must be on or before the event start time.")
        if capacity_raw:
            try:
                capacity = int(capacity_raw)
                if capacity < 1:
                    raise ValueError
            except ValueError:
                errors.append("Capacity must be a positive whole number or left blank.")
        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("admin/event_form.html", event=None)

        event = Event(
            slug=_slugify(title),
            title=title,
            description=description,
            venue=venue,
            start_at=start_at,
            end_at=end_at,
            registration_deadline=deadline,
            capacity=capacity,
            status="draft",
            created_by=current_user.id,
        )
        db.session.add(event)
        db.session.commit()
        flash("Event created as a draft. Review it, then publish registration.", "success")
        return redirect(url_for("admin.event_detail", event_id=event.id))

    return render_template("admin/event_form.html", event=None)


@admin_bp.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        venue = request.form.get("venue", "").strip()
        start_at = _parse_local_datetime(request.form.get("start_at"))
        end_at = _parse_local_datetime(request.form.get("end_at"))
        deadline = _parse_local_datetime(request.form.get("registration_deadline"))
        capacity_raw = request.form.get("capacity", "").strip()
        description = request.form.get("description", "").strip()
        errors = []
        capacity = None
        if len(title) < 3 or not venue:
            errors.append("Event title and venue are required.")
        if not start_at or not end_at or not deadline or end_at <= start_at:
            errors.append("Please check the event dates and times.")
        elif deadline > start_at:
            errors.append("Registration deadline must be on or before the event start time.")
        if capacity_raw:
            try:
                capacity = int(capacity_raw)
                if capacity < event.registration_count or capacity < 1:
                    errors.append("Capacity cannot be lower than the current registration count.")
            except ValueError:
                errors.append("Capacity must be a positive whole number or blank.")
        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("admin/event_form.html", event=event)
        event.title = title
        event.venue = venue
        event.start_at = start_at
        event.end_at = end_at
        event.registration_deadline = deadline
        event.capacity = capacity
        event.description = description
        db.session.commit()
        flash("Event details updated.", "success")
        return redirect(url_for("admin.event_detail", event_id=event.id))
    return render_template("admin/event_form.html", event=event)


@admin_bp.get("/events/<int:event_id>")
@login_required
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    registrations = event.registrations.order_by(Registration.created_at.desc()).limit(150).all()
    logs = CheckInLog.query.filter_by(event_id=event.id).order_by(CheckInLog.scanned_at.desc()).limit(25).all()
    registration_url = f"{current_app.config['APP_BASE_URL']}{url_for('public.register', slug=event.slug)}"
    return render_template("admin/event_detail.html", event=event, registrations=registrations, logs=logs, registration_url=registration_url)


@admin_bp.post("/events/<int:event_id>/publish")
@login_required
def publish_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.status == "cancelled":
        flash("A cancelled event cannot be published.", "danger")
    else:
        event.status = "published"
        db.session.commit()
        flash("Event published. Public registration is now available.", "success")
    return redirect(url_for("admin.event_detail", event_id=event.id))


@admin_bp.post("/events/<int:event_id>/close")
@login_required
def close_event(event_id):
    event = Event.query.get_or_404(event_id)
    event.status = "closed"
    event.checkin_open = False
    db.session.commit()
    flash("Event closed. New registrations and check-ins are disabled.", "success")
    return redirect(url_for("admin.event_detail", event_id=event.id))


@admin_bp.post("/events/<int:event_id>/cancel")
@login_required
def cancel_event(event_id):
    event = Event.query.get_or_404(event_id)
    event.status = "cancelled"
    event.checkin_open = False
    db.session.commit()
    flash("Event cancelled. Check-in has been disabled.", "warning")
    return redirect(url_for("admin.event_detail", event_id=event.id))


@admin_bp.post("/events/<int:event_id>/toggle-checkin")
@login_required
def toggle_checkin(event_id):
    event = Event.query.get_or_404(event_id)
    if event.status != "published":
        flash("Publish the event before opening its gate.", "warning")
    else:
        event.checkin_open = not event.checkin_open
        db.session.commit()
        flash("Check-in gate opened." if event.checkin_open else "Check-in gate closed.", "success")
    return redirect(url_for("admin.event_detail", event_id=event.id))


@admin_bp.post("/registrations/<int:registration_id>/approve")
@login_required
def approve_registration(registration_id):
    registration = Registration.query.get_or_404(registration_id)
    # Lock the event row so concurrent approvals cannot exceed its capacity.
    event = Event.query.filter_by(id=registration.event_id).with_for_update().first_or_404()
    if registration.status == "approved":
        flash("This registration is already approved. Use Resend Ticket to rotate and send a fresh ticket.", "info")
        return redirect(url_for("admin.event_detail", event_id=event.id))
    if registration.status != "pending":
        flash("Only pending registrations can be approved.", "danger")
        return redirect(url_for("admin.event_detail", event_id=event.id))
    if event.status in {"cancelled", "closed"}:
        flash("Registrations cannot be approved for a closed or cancelled event.", "danger")
        return redirect(url_for("admin.event_detail", event_id=event.id))
    if event.capacity is not None and event.approved_count >= event.capacity:
        flash("The event has reached its approved capacity.", "danger")
        return redirect(url_for("admin.event_detail", event_id=event.id))

    registration.status = "approved"
    registration.approved_at = local_now()
    registration.approved_by = current_user.id
    db.session.commit()

    token = create_ticket_token()
    status, message = _ticket_email(registration, event, token)
    if status == "sent":
        flash(f"Registration approved. {message}", "success")
    elif status == "preview":
        flash(f"Registration approved and PDF ticket generated. {message}", "warning")
    else:
        flash(f"Registration approved and PDF ticket generated, but email delivery failed. {message}", "warning")
    return redirect(url_for("admin.event_detail", event_id=event.id))


@admin_bp.post("/registrations/<int:registration_id>/reject")
@login_required
def reject_registration(registration_id):
    registration = Registration.query.get_or_404(registration_id)
    if registration.checked_in_at:
        flash("A checked-in registration cannot be rejected.", "danger")
    else:
        registration.status = "rejected"
        registration.token_hash = None
        db.session.commit()
        flash("Registration rejected. No entry ticket is active.", "success")
    return redirect(url_for("admin.event_detail", event_id=registration.event_id))


@admin_bp.post("/registrations/<int:registration_id>/resend-ticket")
@login_required
def resend_ticket(registration_id):
    registration = Registration.query.get_or_404(registration_id)
    if registration.status != "approved" or registration.checked_in_at:
        flash("A ticket can only be reissued to an approved participant who has not checked in.", "danger")
        return redirect(url_for("admin.event_detail", event_id=registration.event_id))
    token = create_ticket_token()
    status, message = _ticket_email(registration, registration.event, token)
    if status == "sent":
        flash(f"A fresh ticket was generated and emailed. {message}", "success")
    else:
        flash(f"A fresh ticket was generated. {message}", "warning")
    return redirect(url_for("admin.event_detail", event_id=registration.event_id))


@admin_bp.get("/registrations/<int:registration_id>/ticket")
@login_required
def download_ticket(registration_id):
    registration = Registration.query.get_or_404(registration_id)
    if registration.ticket_pdf_data:
        return send_file(
            BytesIO(registration.ticket_pdf_data),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=registration.ticket_pdf or f"{registration.ticket_code}.pdf",
            max_age=0,
        )

    # Backward compatibility for tickets generated by the earlier local-only
    # version. Newly issued tickets are stored as database bytes instead.
    if registration.ticket_pdf:
        ticket_path = Path(current_app.instance_path) / registration.ticket_pdf
        if ticket_path.is_file():
            return send_from_directory(str(ticket_path.parent), ticket_path.name, as_attachment=True)
    abort(404)


@admin_bp.get("/events/<int:event_id>/scanner")
@login_required
def scanner(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template("admin/scanner.html", event=event)


@admin_bp.post("/api/events/<int:event_id>/check-in")
@login_required
def checkin_api(event_id):
    event = Event.query.get_or_404(event_id)
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"ok": False, "status": "invalid", "message": "Invalid request data."}), 400
    qr_payload = data.get("qr_payload", "")
    gate = data.get("gate", "Main Gate")
    if not isinstance(qr_payload, str) or len(qr_payload) > 1000:
        return jsonify({"ok": False, "status": "invalid", "message": "Invalid scan data."}), 400
    if not isinstance(gate, str):
        gate = "Main Gate"
    gate = gate.strip()[:80] or "Main Gate"
    result = process_checkin(event, qr_payload, gate, current_user.id, request.remote_addr)
    status_code = 200 if result.get("ok") else 400
    return jsonify(result), status_code


@admin_bp.get("/events/<int:event_id>/export.csv")
@login_required
def export_csv(event_id):
    event = Event.query.get_or_404(event_id)
    registrations = event.registrations.order_by(Registration.created_at.asc()).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Ticket ID", "Name", "Email", "Phone", "Institution", "Category", "Registration Status", "Check-in Status", "Check-in Time", "Gate"])
    def csv_safe(value):
        value = "" if value is None else str(value)
        return "'" + value if value.startswith(("=", "+", "-", "@", "\t", "\r")) else value

    for item in registrations:
        writer.writerow([csv_safe(value) for value in [
            item.ticket_code or "",
            item.full_name,
            item.email,
            item.phone,
            item.institution,
            item.category,
            item.status,
            "Checked In" if item.checked_in_at else "Not Checked In",
            item.checked_in_at.strftime("%Y-%m-%d %H:%M:%S") if item.checked_in_at else "",
            item.checkin_gate or "",
        ]])
    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f"attachment; filename=event-{event.id}-attendees.csv"
    return response
