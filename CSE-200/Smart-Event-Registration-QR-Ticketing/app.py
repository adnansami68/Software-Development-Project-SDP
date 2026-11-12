"""Vercel WSGI entrypoint. Vercel detects this top-level `app` variable."""
from eventpass import create_app

app = create_app()
