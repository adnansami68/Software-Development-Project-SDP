from datetime import datetime
import os
from zoneinfo import ZoneInfo

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def local_now() -> datetime:
    """Return current time in configured local timezone as a naive DB value."""
    timezone_name = os.getenv("TIMEZONE", "Asia/Dhaka")
    return datetime.now(ZoneInfo(timezone_name)).replace(tzinfo=None)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=local_now)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    venue = db.Column(db.String(180), nullable=False)
    start_at = db.Column(db.DateTime, nullable=False)
    end_at = db.Column(db.DateTime, nullable=False)
    registration_deadline = db.Column(db.DateTime, nullable=False)
    capacity = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="draft")  # draft/published/closed/cancelled
    checkin_open = db.Column(db.Boolean, nullable=False, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=local_now)

    creator = db.relationship("User", backref=db.backref("events", lazy=True))
    registrations = db.relationship(
        "Registration", back_populates="event", cascade="all, delete-orphan", lazy="dynamic"
    )

    @property
    def approved_count(self) -> int:
        return self.registrations.filter_by(status="approved").count()

    @property
    def registration_count(self) -> int:
        return self.registrations.filter(Registration.status.in_(["pending", "approved"])).count()

    @property
    def checked_in_count(self) -> int:
        return self.registrations.filter(Registration.checked_in_at.isnot(None)).count()

    @property
    def remaining_seats(self):
        if self.capacity is None:
            return None
        return max(self.capacity - self.registration_count, 0)


class Registration(db.Model):
    __tablename__ = "registrations"
    __table_args__ = (
        db.UniqueConstraint("event_id", "email", name="uq_registration_event_email"),
        db.UniqueConstraint("event_id", "student_id", name="uq_registration_event_student"),
    )

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    full_name = db.Column(db.String(140), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
    phone = db.Column(db.String(40), nullable=False)
    institution = db.Column(db.String(180), nullable=False, default="")
    student_id = db.Column(db.String(80), nullable=True)
    category = db.Column(db.String(80), nullable=False, default="Participant")
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending/approved/rejected/cancelled
    ticket_code = db.Column(db.String(40), unique=True, nullable=True, index=True)
    token_hash = db.Column(db.String(64), unique=True, nullable=True, index=True)
    ticket_pdf = db.Column(db.String(255), nullable=True)
    ticket_pdf_data = db.Column(db.LargeBinary, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=local_now)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    checked_in_at = db.Column(db.DateTime, nullable=True)
    checkin_gate = db.Column(db.String(80), nullable=True)
    checked_in_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    event = db.relationship("Event", back_populates="registrations")
    approver = db.relationship("User", foreign_keys=[approved_by])
    checkin_operator = db.relationship("User", foreign_keys=[checked_in_by])


class CheckInLog(db.Model):
    __tablename__ = "checkin_logs"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    registration_id = db.Column(db.Integer, db.ForeignKey("registrations.id", ondelete="SET NULL"), nullable=True)
    ticket_code = db.Column(db.String(40), nullable=True)
    gate = db.Column(db.String(80), nullable=False, default="Main Gate")
    result = db.Column(db.String(20), nullable=False)  # valid/duplicate/invalid/closed
    message = db.Column(db.String(255), nullable=False)
    scanned_at = db.Column(db.DateTime, nullable=False, default=local_now)
    scanned_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    source_ip = db.Column(db.String(64), nullable=True)

    event = db.relationship("Event")
    registration = db.relationship("Registration")
    operator = db.relationship("User")
