import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from eventpass import create_app
from eventpass.extensions import db
from eventpass.models import Event, Registration, User, local_now
from eventpass.services.security import make_qr_payload
import eventpass.blueprints.admin as admin_routes


class EventPassFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret-key-for-unit-tests",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "MAIL_SUPPRESS_SEND": True,
            "APP_BASE_URL": "http://localhost",
        })
        self.app.instance_path = self.tmp.name
        Path(self.tmp.name, "outbox").mkdir(exist_ok=True)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            admin = User(name="Test Organizer", email="organizer@example.com")
            admin.set_password("TestPassword123!")
            db.session.add(admin)
            db.session.flush()
            start = local_now() + timedelta(days=10)
            self.event = Event(
                slug="test-event-2026",
                title="Test Event 2026",
                description="Unit test event",
                venue="Test Hall",
                start_at=start,
                end_at=start + timedelta(hours=3),
                registration_deadline=start - timedelta(days=1),
                capacity=10,
                status="published",
                checkin_open=True,
                created_by=admin.id,
            )
            db.session.add(self.event)
            db.session.commit()
            self.event_id = self.event.id
            self.event_slug = self.event.slug
        self.client.post("/auth/login", data={"email": "organizer@example.com", "password": "TestPassword123!"}, follow_redirects=True)

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.tmp.cleanup()

    def register_participant(self, email="participant@example.com"):
        return self.client.post(
            f"/e/{self.event_slug}",
            data={
                "full_name": "Test Participant",
                "email": email,
                "phone": "01700000000",
                "institution": "BUBT",
                "student_id": "TEST-001" if email == "participant@example.com" else "TEST-002",
                "category": "Participant",
            },
            follow_redirects=True,
        )

    def test_registration_is_saved_as_pending(self):
        response = self.register_participant()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"REGISTRATION RECEIVED", response.data)
        with self.app.app_context():
            registration = Registration.query.filter_by(email="participant@example.com").first()
            self.assertIsNotNone(registration)
            self.assertEqual(registration.status, "pending")
            self.assertIsNone(registration.token_hash)

    def test_duplicate_email_registration_is_blocked(self):
        self.register_participant()
        response = self.register_participant()
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            count = Registration.query.filter_by(email="participant@example.com").count()
            self.assertEqual(count, 1)

    def test_approval_and_one_time_checkin(self):
        self.register_participant()
        with self.app.app_context():
            registration = Registration.query.filter_by(email="participant@example.com").first()
            registration_id = registration.id

        fixed_token = "unit-test-secure-token-123456789"
        original_token_factory = admin_routes.create_ticket_token
        admin_routes.create_ticket_token = lambda: fixed_token
        try:
            response = self.client.post(f"/admin/registrations/{registration_id}/approve", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
        finally:
            admin_routes.create_ticket_token = original_token_factory

        payload = make_qr_payload(self.event_slug, fixed_token)
        first = self.client.post(
            f"/admin/api/events/{self.event_id}/check-in",
            json={"qr_payload": payload, "gate": "Gate A"},
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json["status"], "valid")

        second = self.client.post(
            f"/admin/api/events/{self.event_id}/check-in",
            json={"qr_payload": payload, "gate": "Gate B"},
        )
        self.assertEqual(second.status_code, 400)
        self.assertEqual(second.json["status"], "duplicate")

        with self.app.app_context():
            registration = db.session.get(Registration, registration_id)
            self.assertIsNotNone(registration.checked_in_at)
            self.assertEqual(registration.checkin_gate, "Gate A")
            self.assertTrue(registration.ticket_pdf_data.startswith(b"%PDF"))
            self.assertTrue((Path(self.app.instance_path) / "outbox" / f"ticket-{registration.id}.eml").is_file())
            ticket_id = registration.id

        download = self.client.get(f"/admin/registrations/{ticket_id}/ticket")
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.mimetype, "application/pdf")
        self.assertTrue(download.data.startswith(b"%PDF"))

    def test_health_endpoint_reports_database_connection(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")
        self.assertEqual(response.json["database"], "connected")

    def test_wrong_event_qr_is_rejected(self):
        self.register_participant()
        payload = make_qr_payload("another-event", "fake-token")
        response = self.client.post(
            f"/admin/api/events/{self.event_id}/check-in",
            json={"qr_payload": payload, "gate": "Main Gate"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["status"], "invalid")


if __name__ == "__main__":
    unittest.main(verbosity=2)
