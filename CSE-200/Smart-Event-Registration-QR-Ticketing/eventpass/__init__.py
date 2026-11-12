"""EventPass Flask application factory."""

from datetime import datetime
import os
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, render_template
from flask_login import current_user
from sqlalchemy import text

from .config import Config
from .extensions import csrf, db, login_manager


@login_manager.user_loader
def load_user(user_id):
    from .models import User
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


def create_app(test_config=None):
    is_vercel = Config.IS_VERCEL
    if is_vercel:
        # Vercel's deployment filesystem is read-only; /tmp is writable but
        # ephemeral. Persistent application records and PDFs live in Postgres.
        instance_dir = Path(os.getenv("EVENTPASS_INSTANCE_DIR", "/tmp/eventpass-instance"))
        instance_dir.mkdir(parents=True, exist_ok=True)
        app = Flask(__name__, instance_relative_config=True, instance_path=str(instance_dir))
    else:
        app = Flask(__name__, instance_relative_config=True)

    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    (Path(app.instance_path) / "outbox").mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please sign in to access the organizer dashboard."
    login_manager.login_message_category = "info"
    csrf.init_app(app)

    from .blueprints.auth import auth_bp
    from .blueprints.public import public_bp
    from .blueprints.admin import admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    @app.context_processor
    def inject_globals():
        return {
            "app_name": app.config.get("APP_NAME", "EventPass"),
            "current_year": datetime.now(ZoneInfo(app.config.get("TIMEZONE", "Asia/Dhaka"))).year,
            "logged_in_user": current_user,
        }

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(self), microphone=()")
        if request_is_sensitive(response):
            response.headers.setdefault("Cache-Control", "no-store")
        return response

    @app.get("/health")
    def health():
        try:
            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1 FROM users LIMIT 1"))
            return jsonify({"status": "ok", "database": "connected"}), 200
        except Exception:
            app.logger.exception("Health check could not connect to the database")
            return jsonify({"status": "error", "database": "unavailable"}), 503

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_error):
        db.session.rollback()
        app.logger.exception("Unhandled application error")
        return render_template("errors/500.html"), 500

    if app.config.get("AUTO_CREATE_DB"):
        from .db_setup import initialize_database
        with app.app_context():
            initialize_database()

    return app


def request_is_sensitive(response) -> bool:
    """Avoid caching dynamic HTML and authenticated/admin responses."""
    content_type = response.headers.get("Content-Type", "")
    return "text/html" in content_type or response.headers.get("Set-Cookie") is not None
