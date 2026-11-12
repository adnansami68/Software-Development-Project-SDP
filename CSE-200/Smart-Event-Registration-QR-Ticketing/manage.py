"""Command-line management for EventPass.

Examples:
    python manage.py init-db
    python manage.py create-admin
    python manage.py seed-demo
    python manage.py test

For a production database, pass a separate, uncommitted env file:
    python manage.py --env-file .env.production init-db
"""

import argparse
import getpass
import sys
from datetime import timedelta

from dotenv import load_dotenv


def build_parser():
    parser = argparse.ArgumentParser(description="EventPass project management utility")
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Environment file to load (default: .env). Never commit secret env files.",
    )
    parser.add_argument(
        "command",
        choices=["init-db", "create-admin", "seed-demo", "run", "test"],
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    load_dotenv(args.env_file, override=True)

    # Import after loading the requested environment file so DATABASE_URL,
    # SECRET_KEY and other settings are applied before the Flask app is built.
    from eventpass import create_app
    from eventpass.db_setup import initialize_database
    from eventpass.extensions import db
    from eventpass.models import Event, User, local_now

    app = create_app()

    if args.command == "init-db":
        with app.app_context():
            initialize_database()
            print("Database initialized successfully.")
            print(f"Database dialect: {db.engine.dialect.name}")
        return 0

    if args.command == "create-admin":
        with app.app_context():
            initialize_database()
            print("\nCreate EventPass organizer account")
            name = input("Full name: ").strip()
            email = input("Email address: ").strip().lower()
            if not name or "@" not in email:
                print("A name and valid email address are required.")
                return 1
            if User.query.filter_by(email=email).first():
                print("An account with this email already exists.")
                return 1
            password = getpass.getpass("Password (minimum 10 characters): ")
            confirmation = getpass.getpass("Confirm password: ")
            if len(password) < 10:
                print("Password must be at least 10 characters long.")
                return 1
            if password != confirmation:
                print("Passwords do not match.")
                return 1
            user = User(name=name, email=email, is_active=True)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            print(f"Organizer account created for {email}.")
        return 0

    if args.command == "seed-demo":
        with app.app_context():
            initialize_database()
            admin = User.query.order_by(User.id.asc()).first()
            if not admin:
                print("Create an organizer first: python manage.py create-admin")
                return 1
            if Event.query.filter_by(slug="eventpass-demo-day").first():
                print("Demo event already exists.")
                return 0
            start = local_now() + timedelta(days=14)
            end = start + timedelta(hours=6)
            event = Event(
                slug="eventpass-demo-day",
                title="EventPass Demo Day",
                description="A sample event for testing registration, organizer approval, QR ticket delivery and gate check-in.",
                venue="BUBT Campus — Demo Hall",
                start_at=start,
                end_at=end,
                registration_deadline=start - timedelta(days=1),
                capacity=200,
                status="published",
                checkin_open=False,
                created_by=admin.id,
            )
            db.session.add(event)
            db.session.commit()
            print("Demo event created and published.")
            print(f"Registration URL: {app.config['APP_BASE_URL']}/e/{event.slug}")
        return 0

    if args.command == "run":
        app.run(host="127.0.0.1", port=5000, debug=False)
        return 0

    if args.command == "test":
        import unittest
        suite = unittest.defaultTestLoader.discover("tests")
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
