# EventPass — Smart Event Registration, QR Ticketing & Entry Validation

EventPass is a Python Flask web application for managing events from registration to gate check-in. Participants register through a public event page. Organizers review registrations, approve participants, issue QR tickets by email, and validate tickets at one or more entry gates. A ticket can be checked in only once.

## Main features

- Organizer login and dashboard
- Multiple event creation, editing, publishing, closing, and cancellation
- Public participant registration with duplicate email / participant-ID checks
- Organizer approval and rejection workflow
- Cryptographically random QR ticket tokens; only SHA-256 token hashes are stored
- Printable PDF ticket with QR code, stored as a database BLOB (not on the deployment filesystem)
- Email delivery with inline QR and PDF attachment through SMTP
- Browser camera scanner and manual payload fallback
- Atomic one-time check-in, duplicate / invalid / closed scan logging
- CSV attendee export and event activity history
- Local SQLite development and PostgreSQL production support

## Technology

- Python 3.12+ (local Python 3.14 is also supported by the current Vercel runtime)
- Flask, Flask-Login, Flask-WTF
- SQLAlchemy / Flask-SQLAlchemy
- SQLite locally; PostgreSQL (Neon recommended) in production
- qrcode, Pillow, ReportLab
- Vanilla JavaScript + `html5-qrcode` for browser scanning

## Run locally on Windows

1. Install Python 3.12 or newer and Git (Git is only needed for GitHub).
2. Extract this repository to a folder such as `C:\SDP\EventPass`.
3. Double-click `setup_windows.bat`. It creates `.venv`, installs dependencies, creates `.env`, and initializes the local SQLite database.
4. Double-click `create_admin.bat` and create the first organizer account.
5. Double-click `run_windows.bat`.
6. Open <http://127.0.0.1:5000>.

Run automated tests with `test_windows.bat`, or:

```powershell
.venv\Scripts\activate
python manage.py test
```

## Production architecture (Vercel)

Do **not** use SQLite as the production database on Vercel. Vercel Functions have a read-only deployment filesystem with only temporary `/tmp` storage. EventPass therefore uses PostgreSQL for durable records and stores generated PDF bytes in the `registrations.ticket_pdf_data` database column.

Recommended stack:

- GitHub: source control
- Vercel: Flask hosting and HTTPS
- Neon PostgreSQL: persistent production database (use the pooled connection URL for runtime)
- SMTP provider: transactional email delivery

### Required production environment variables

| Variable | Example / purpose |
|---|---|
| `SECRET_KEY` | Long random secret; never commit it |
| `DATABASE_URL` | Neon pooled PostgreSQL URL; hostname normally contains `-pooler` |
| `APP_BASE_URL` | `https://your-project.vercel.app` |
| `TIMEZONE` | `Asia/Dhaka` |
| `AUTO_CREATE_DB` | `false` after running the one-time schema setup |
| `SESSION_COOKIE_SECURE` | `true` |
| `MAIL_SERVER` | SMTP host from your email provider |
| `MAIL_PORT` | Usually `587` with STARTTLS or `465` with SSL |
| `MAIL_USE_TLS` | `true` for port 587 |
| `MAIL_USE_SSL` | `false` for port 587 |
| `MAIL_USERNAME` | SMTP username |
| `MAIL_PASSWORD` | SMTP password / provider SMTP key |
| `MAIL_DEFAULT_SENDER` | Verified sender address |
| `MAIL_SUPPRESS_SEND` | `false` |

Copy `.env.production.example` to `.env.production` locally when initializing a production database. Do not commit `.env.production`.

### Initialize Neon and create the production organizer

1. Create a PostgreSQL database with Neon (or another PostgreSQL provider). Copy the **direct** connection URL for one-time schema/admin commands.
2. Copy `.env.production.example` to `.env.production` and fill in the direct `DATABASE_URL`, a new `SECRET_KEY`, and your production `APP_BASE_URL`.
3. From the repository root, run:

```powershell
.venv\Scripts\activate
python manage.py --env-file .env.production init-db
python manage.py --env-file .env.production create-admin
```

4. In Vercel, connect the Neon Marketplace integration or add the **pooled** Neon connection URL as `DATABASE_URL`. The runtime URL should use the `-pooler` hostname. Add the remaining production environment variables in Vercel Project Settings → Environment Variables.
5. Set `AUTO_CREATE_DB=false` in Vercel because the schema has already been initialized. Set the variables for Production and Preview as appropriate.
6. Never place database URLs, SMTP passwords, or `SECRET_KEY` in source code or GitHub.

### Push to GitHub

Create an empty repository on GitHub, then run the following from the project root. Replace the URL with your repository URL:

```bash
git init -b main
git add .
git status --short
git commit -m "Initial EventPass release"
git remote add origin https://github.com/YOUR-USERNAME/eventpass-sdp.git
git push -u origin main
```

Before committing, confirm that `.env`, `.env.production`, `.venv`, `instance/`, `*.db`, and generated PDFs are not staged. The included `.gitignore` excludes them.

### Deploy from GitHub to Vercel

1. Sign in to Vercel and choose **Add New → Project**.
2. Import the GitHub repository.
3. Vercel should detect Flask from `requirements.txt` and the root `app.py` WSGI entry point. Keep build/output settings on automatic unless Vercel displays a specific configuration error.
4. Add the production environment variables described above.
5. Deploy. After deployment, open `https://your-project.vercel.app/health`; the expected response is `{"status":"ok","database":"connected"}`.
6. Open the homepage and log in using the organizer account created against the same Neon database.

Vercel's Python runtime supports Python 3.12, 3.13 and 3.14. The repository pins Vercel to 3.12 via `.python-version` for a conservative deployment baseline. The `app.py` file exports the Flask instance as `app`, which is the entry point Vercel detects.

## Email notes

Local development works without SMTP: messages are written as `.eml` previews under `instance/outbox/`. On Vercel, the filesystem is ephemeral, so preview messages are logged but not saved as durable files. Configure an SMTP provider to deliver real tickets. Vercel recommends using an external transactional email provider; Gmail App Passwords are best treated as a development/test option. The sender address must be verified by your email provider.

## Camera / scanner notes

- Camera access works on `localhost` during local development.
- On a hosted site, use the HTTPS Vercel URL and allow camera access in the browser.
- Gate operators must sign in. All gates must use the same deployed application and PostgreSQL database.
- A successful check-in is written once using a conditional database update. A second scan is logged as a duplicate and rejected.

## Database and migrations

`init-db` creates missing tables and applies the included compatibility migration for the `ticket_pdf_data` column. `create_all()` does not automatically migrate arbitrary future model changes. For future schema changes, add and apply a versioned Alembic/Flask-Migrate migration before deploying the new code.

## Project structure

```text
app.py                       # Vercel WSGI entry point
manage.py                    # CLI: init-db, create-admin, seed-demo, run, test
run.py                       # Local WSGI development entry point
eventpass/
  blueprints/                 # Public, authentication, organizer routes
  services/                   # QR, PDF, email, ticket security, check-in
  templates/                  # Jinja HTML pages
  static/                     # CSS and JavaScript
  models.py                   # SQLAlchemy models
docs/                         # Architecture, test plan, report and viva guides
tests/                        # Automated application flow tests
```

## Academic use

This project is an SDP prototype. Before using it for a real paid / high-volume event, review security, privacy, load limits, email-provider policies, backups, and operational procedures. QR possession does not prove the attendee's identity; gate staff should verify identity where event policy requires it.
