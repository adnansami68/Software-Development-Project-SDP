"""Small, explicit schema bootstrap and compatibility helpers."""

from sqlalchemy import inspect, text

from .extensions import db


def ensure_compatibility_columns() -> None:
    """Add columns introduced after the first local prototype was created.

    `create_all()` creates new tables but does not alter existing ones. This
    compatibility migration preserves existing local SQLite demo data while
    adding the binary PDF column used by the Vercel-safe ticket workflow.
    Future structural changes should be recorded as proper Alembic migrations.
    """
    inspector = inspect(db.engine)
    if "registrations" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("registrations")}
    if "ticket_pdf_data" in columns:
        return

    dialect = db.engine.dialect.name
    if dialect == "sqlite":
        statement = "ALTER TABLE registrations ADD COLUMN ticket_pdf_data BLOB"
    elif dialect == "postgresql":
        statement = "ALTER TABLE registrations ADD COLUMN IF NOT EXISTS ticket_pdf_data BYTEA"
    else:
        raise RuntimeError(f"Unsupported database dialect for compatibility migration: {dialect}")

    with db.engine.begin() as connection:
        connection.execute(text(statement))


def initialize_database() -> None:
    db.create_all()
    ensure_compatibility_columns()
