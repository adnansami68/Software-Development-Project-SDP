import re
from datetime import datetime

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Event, Registration, local_now
from ..services.mailer import send_registration_received


public_bp = Blueprint("public", __name__)


def _is_valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value or ""))


@public_bp.get("/")
def index():
    now = local_now()
    events = (
        Event.query.filter_by(status="published")
        .filter(Event.registration_deadline >= now)
        .order_by(Event.start_at.asc())
        .limit(6)
        .all()
    )
    return render_template("public/index.html", events=events)


@public_bp.get("/events")
def events():
    items = Event.query.filter_by(status="published").order_by(Event.start_at.asc()).all()
    return render_template("public/events.html", events=items)


@public_bp.route("/e/<slug>", methods=["GET", "POST"])
def register(slug):
    event_query = Event.query.filter_by(slug=slug)
    # On PostgreSQL, serialize registrations for the same event while checking
    # capacity so simultaneous requests cannot reserve more seats than allowed.
    event = (event_query.with_for_update().first_or_404()
             if request.method == "POST" else event_query.first_or_404())
    now = local_now()
    can_register = event.status == "published" and event.registration_deadline >= now
    if event.capacity is not None and event.registration_count >= event.capacity:
        can_register = False

    if request.method == "POST":
        if not can_register:
            flash("Registration is currently closed for this event.", "warning")
            return redirect(url_for("public.register", slug=slug))

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        institution = request.form.get("institution", "").strip()
        student_id = request.form.get("student_id", "").strip() or None
        category = request.form.get("category", "Participant").strip() or "Participant"

        errors = []
        if len(full_name) < 2:
            errors.append("Please enter your full name.")
        if not _is_valid_email(email):
            errors.append("Please enter a valid email address.")
        if len(phone) < 7:
            errors.append("Please enter a valid phone number.")
        if (len(full_name) > 140 or len(email) > 255 or len(phone) > 40
                or len(institution) > 180 or (student_id and len(student_id) > 80) or len(category) > 80):
            errors.append("One or more fields exceed the allowed length.")
        if category not in {"Participant", "Guest", "Volunteer", "Speaker", "Organizer"}:
            errors.append("Please choose a valid participant category.")

        if Registration.query.filter_by(event_id=event.id, email=email).first():
            errors.append("This email address has already been registered for this event.")
        if student_id and Registration.query.filter_by(event_id=event.id, student_id=student_id).first():
            errors.append("This student/participant ID has already been registered for this event.")
        if event.capacity is not None and event.registration_count >= event.capacity:
            errors.append("All event seats have been reserved.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("public/register.html", event=event, can_register=can_register)

        registration = Registration(
            event_id=event.id,
            full_name=full_name,
            email=email,
            phone=phone,
            institution=institution,
            student_id=student_id,
            category=category,
            status="pending",
        )
        db.session.add(registration)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("A registration with these details already exists.", "danger")
            return redirect(url_for("public.register", slug=slug))

        mail_status, mail_message = send_registration_received(registration, event)
        current_app.logger.info("Registration acknowledgement: %s (%s)", registration.id, mail_status)
        return render_template("public/registration_success.html", event=event, registration=registration, mail_status=mail_status)

    return render_template("public/register.html", event=event, can_register=can_register)
