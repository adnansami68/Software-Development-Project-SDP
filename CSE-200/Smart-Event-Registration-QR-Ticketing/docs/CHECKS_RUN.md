# Build and validation notes

Checks completed for this release in the authoring environment:

- All Python source files passed `python -m py_compile`.
- Both frontend JavaScript files passed `node --check`.
- The in-memory QR generator produced a valid PNG.
- The in-memory PDF ticket generator produced a valid PDF (`%PDF` header).
- The email MIME smoke test verified the message contains `text/plain`, `text/html`, an inline `image/png` QR part, and an `application/pdf` attachment. This specifically covers the earlier `NoneType.add_related` approval bug.
- Static structure checks confirmed the Vercel entry point, PostgreSQL configuration, local/production environment templates, and the Vercel-safe `/tmp` instance path are present.

**Not verified in this authoring environment:** the complete Flask integration suite, live Neon connection, real SMTP delivery and live Vercel deployment were not executed because Flask, Flask-SQLAlchemy, Flask-Login and Flask-WTF are not installed in this authoring runtime, and package installation was unavailable. The integration tests are included in `tests/test_app.py`. Run `setup_windows.bat` and then `test_windows.bat` on the team's Windows PC. Before using this for a real event, verify Neon connectivity, actual SMTP delivery, HTTPS camera permission, concurrency at all gates, backups and organizer access controls.
