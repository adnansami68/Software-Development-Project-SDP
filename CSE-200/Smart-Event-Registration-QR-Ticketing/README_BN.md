# EventPass — Smart Event Registration, QR Ticketing & Entry Validation System

**EventPass** হলো Python Flask দিয়ে তৈরি একটি Event Management Web Application। Participant অনলাইনে Registration করবে, Organizer Registration Approve করলে Unique QR Ticket তৈরি হবে, Email-এ QR ও PDF Ticket যাবে, এবং Event Gate-এ Scan করলে Ticket Valid / Invalid / Already Used দেখাবে। একটি Ticket দিয়ে একবারই Entry নেওয়া যাবে।

## ১. Project-এর Feature

- Organizer Login ও Dashboard
- একাধিক Event Create, Edit, Publish, Close ও Cancel
- Public Participant Registration
- একই Event-এ Duplicate Email / Student ID Registration আটকানো
- Admin Approval ও Rejection
- নিরাপদ Random QR Ticket Token
- Printable PDF Entry Pass
- QR সহ Email এবং PDF Attachment
- Laptop / Mobile Browser Camera Scanner
- Manual QR Payload দিয়ে Backup Validation
- Valid, Invalid, Duplicate, Closed Scan Log
- CSV Attendee Export
- একবারের বেশি একই Ticket দিয়ে Entry আটকানো
- Local SQLite এবং Production PostgreSQL Support

## ২. Technology

| Technology | ব্যবহার |
|---|---|
| Python 3.12+ | Backend Programming |
| Flask | Web Application |
| HTML, CSS, JavaScript | Frontend |
| Flask-Login | Organizer Login |
| Flask-WTF | CSRF Protection |
| SQLAlchemy | Database ORM |
| SQLite | Local Development Database |
| PostgreSQL / Neon | Production Database |
| qrcode + Pillow | QR Generate |
| ReportLab | PDF Ticket |
| SMTP | Email Delivery |

## ৩. Windows-এ Local Setup

১. ZIP Extract করে `C:\SDP\EventPass` অথবা `E:\EventPass`-এর মতো একটি Folder-এ রাখো।

২. `setup_windows.bat` Double Click করো। এটি:
- `.venv` Virtual Environment তৈরি করবে
- `requirements.txt` থেকে Package Install করবে
- `.env` তৈরি করবে
- Local SQLite Database Initialize করবে

৩. `create_admin.bat` চালিয়ে Organizer Account তৈরি করবে।

৪. `run_windows.bat` চালাও। Terminal খোলা রাখবে।

৫. Chrome-এ Open করো:

```text
http://127.0.0.1:5000
```

৬. Admin Login করে Event Create করো, Publish করো, Public Registration Link দিয়ে Participant Registration করো, তারপর Approve করে Ticket তৈরি করো।

### Test চালানো

```powershell
.venv\Scripts\activate
python manage.py test
```

অথবা `test_windows.bat` Double Click করো।

## ৪. পুরোনো Local Project থেকে নতুন Version-এ আসা

আগের Local Project-এ Event বা Registration Data থাকলে সেটি Delete করবে না। পুরোনো Project-এর `instance` Folder Backup রাখবে। নতুন Project Folder-এ পুরোনো `instance` Folder Copy করলে Local SQLite Database ও পুরোনো Ticket Files রাখা যাবে। এরপর নতুন Project-এ `setup_windows.bat` চালালে `ticket_pdf_data` Compatibility Column যোগ হবে। নতুন Ticket PDF Database-এ সংরক্ষিত হবে।

নতুন Project Folder-এ `.env` নতুন করে তৈরি করাই ভালো। পুরোনো `.env` অন্ধভাবে Copy করবে না।

## ৫. Vercel-এ কেন PostgreSQL লাগবে?

Vercel Function-এর Deployment Filesystem Read-only; শুধু অস্থায়ী `/tmp` Storage লেখা যায়। তাই Vercel-এ SQLite Database File বা local PDF Folder-এ নির্ভর করা যাবে না। EventPass Production-এ PostgreSQL ব্যবহার করবে এবং PDF bytes Database-এ রাখবে।

প্রস্তাবিত Architecture:

```text
GitHub Repository
       |
       v
Vercel (Flask / Python Hosting)
       |
       +------ Neon PostgreSQL (Permanent Data)
       |
       +------ SMTP Provider (Email + PDF Ticket)
```

## ৬. Neon PostgreSQL Database তৈরি

১. <https://neon.tech> এ Account তৈরি করো।

২. New Project তৈরি করো। Region নির্বাচন করো। সম্ভব হলে তোমাদের User / Vercel Function-এর কাছাকাছি Region নেবে।

৩. Neon Dashboard থেকে **Connect** চাপো।

৪. প্রথমবার Database Schema Initialize করার জন্য **Direct Connection URL** Copy করো। Production Vercel Runtime-এর জন্য পরে **Pooled Connection URL** ব্যবহার করবে—এর Hostname-এ সাধারণত `-pooler` থাকবে।

৫. Project Folder-এ `.env.production.example` Copy করে `.env.production` নামে Save করো।

৬. `.env.production`-এ Direct Database URL, নতুন Secret Key ও Production URL বসাও। উদাহরণ:

```env
SECRET_KEY=এখানে_নতুন_লম্বা_random_secret
APP_NAME=EventPass
APP_BASE_URL=https://your-project.vercel.app
TIMEZONE=Asia/Dhaka
AUTO_CREATE_DB=false
DATABASE_URL=postgresql://USER:PASSWORD@DIRECT-HOST/DBNAME?sslmode=require
```

Secret Key তৈরি করতে Local Terminal-এ চালাতে পারো:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

**Database URL ও Secret Key কাউকে পাঠাবে না এবং GitHub-এ Upload করবে না।**

## ৭. Production Database Initialize ও Admin তৈরি

Local Project Folder-এর CMD / PowerShell-এ চালাও:

```powershell
.venv\Scripts\activate
python manage.py --env-file .env.production init-db
```

সফল হলে `Database initialized successfully.` দেখাবে। এবার Production Database-এই Admin তৈরি করো:

```powershell
python manage.py --env-file .env.production create-admin
```

Admin Name, Email ও Password দেবে। এই Account-ই Deploy করা Website-এ Login করবে।

`init-db` ও `create-admin` Command-এ Direct Database URL ব্যবহার করো। Vercel Runtime-এর জন্য pooled URL ব্যবহার করবে।

## ৮. Email Configuration

Local Demo-তে SMTP না দিলেও PDF Ticket Generate হবে এবং Email Preview `instance/outbox/` Folder-এ থাকবে। বাস্তবে Email পাঠাতে SMTP Credentials লাগবে। Production-এর জন্য Resend SMTP, Postmark, SendGrid বা Amazon SES-এর মতো Transactional Email Provider ব্যবহার করা ভালো। Vercel-এর Documentation-ও External Email Provider Recommend করে।

Vercel Environment Variables-এ এগুলো রাখবে:

```env
MAIL_SERVER=তোমার_SMTP_HOST
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=তোমার_SMTP_USERNAME
MAIL_PASSWORD=তোমার_SMTP_PASSWORD_OR_KEY
MAIL_DEFAULT_SENDER=verified-sender@yourdomain.com
MAIL_SUPPRESS_SEND=false
MAIL_TIMEOUT=15
```

Gmail দিয়ে Testing করলে Google App Password লাগবে; সাধারণ Gmail Password ব্যবহার করবে না। Provider-এর Sender Address Verify করতে হবে।

## ৯. GitHub-এ সুন্দরভাবে Code Upload

১. GitHub-এ Login করো।

২. New Repository তৈরি করো, নাম দিতে পারো `eventpass-sdp`।

৩. Repository Public বা Private করতে পারো। `.env` ও Secret File কোনো অবস্থাতেই Commit করবে না।

৪. Project Folder-এর Terminal-এ নিচের Command চালাও (নিজের GitHub URL বসাবে):

```bash
git init -b main
git add .
git status --short
git commit -m "Initial EventPass release"
git remote add origin https://github.com/YOUR-USERNAME/eventpass-sdp.git
git push -u origin main
```

`git status --short` দেখে নিশ্চিত হবে `.env`, `.env.production`, `.venv`, `instance/` বা Database File Stage হয়নি। `.gitignore` এগুলো বাদ রাখে।

## ১০. GitHub থেকে Vercel Deploy

১. <https://vercel.com> এ Login করো।

২. **Add New → Project** চাপো।

৩. GitHub Connect করে `eventpass-sdp` Repository Import করো।

৪. Vercel Flask Automatically Detect করার কথা, কারণ Root Folder-এ `app.py` আছে এবং সেখানে `app = create_app()` Export করা হয়েছে। Build Command ও Output Directory Automatic রাখবে—Vercel আলাদা কিছু না চাইলে নিজে থেকে সেট করবে না।

৫. Project Settings → Environment Variables-এ Production Variables যোগ করো:

| Variable | Value |
|---|---|
| `SECRET_KEY` | নতুন Random Secret |
| `DATABASE_URL` | Neon-এর Pooled PostgreSQL URL (`-pooler`) |
| `APP_BASE_URL` | `https://your-project.vercel.app` |
| `TIMEZONE` | `Asia/Dhaka` |
| `AUTO_CREATE_DB` | `false` |
| `SESSION_COOKIE_SECURE` | `true` |
| `MAIL_SERVER` | SMTP Provider Host |
| `MAIL_PORT` | `587` |
| `MAIL_USE_TLS` | `true` |
| `MAIL_USE_SSL` | `false` |
| `MAIL_USERNAME` | SMTP Username |
| `MAIL_PASSWORD` | SMTP Password / API Key |
| `MAIL_DEFAULT_SENDER` | Verified Sender Email |
| `MAIL_SUPPRESS_SEND` | `false` |

Neon Marketplace Integration ব্যবহার করলে Vercel নিজে Environment Variable Inject করতে পারে। Manually দিলে Runtime-এর জন্য Pooled URL ব্যবহার করো।

৬. Deploy চাপো। Deploy Complete হলে Vercel URL Open করো।

৭. Database Connection Check:

```text
https://your-project.vercel.app/health
```

Expected response:

```json
{"status":"ok","database":"connected"}
```

৮. এরপর Website-এ Production Database-এ তৈরি করা Organizer Email ও Password দিয়ে Login করো।

## ১১. Scanner কীভাবে ব্যবহার করবে?

- Organizer Login করবে।
- Event Workspace-এ **Open Check-in** করবে।
- **Open Scanner** চাপবে।
- Gate Name লিখবে, যেমন `Main Gate` বা `Gate A`।
- Start Camera চাপবে এবং Browser Permission Allow করবে।
- HTTPS Vercel URL থেকে Mobile Camera-ও ব্যবহার করা যাবে। Local Development-এ `localhost` Camera Permission পায়।
- একই Event-এর সব Gate একই Hosted Application ব্যবহার করবে; ফলে একই Ticket দ্বিতীয় Gate-এ Scan করলেও Duplicate দেখাবে।

## ১২. Project Folder Structure

```text
EventPass/
├── app.py
├── manage.py
├── run.py
├── requirements.txt
├── vercel.json
├── .python-version
├── .env.example
├── .env.production.example
├── eventpass/
│   ├── blueprints/
│   ├── services/
│   ├── templates/
│   ├── static/
│   ├── models.py
│   ├── config.py
│   └── db_setup.py
├── docs/
├── tests/
└── .github/workflows/
```

## ১৩. গুরুত্বপূর্ণ Security / Deployment Note

- QR-এ Participant-এর ব্যক্তিগত তথ্য রাখা হয় না; শুধু Random Token থাকে। Database-এ Token-এর SHA-256 Hash রাখা হয়।
- এক Ticket একবারই Check-in হতে পারে; database update atomically করা হয়।
- QR Code অন্যকে পাঠানো হলে সে আগে Scan করতে পারে। High-security Event-এ Gate Staff পরিচয়পত্র যাচাই করবে।
- সব Gate-এর জন্য একই Server ও Database ব্যবহার করতে হবে।
- Public Site-এ Camera চালাতে HTTPS প্রয়োজন; Vercel URL HTTPS দেয়।
- Secret / Database URL / SMTP Password GitHub-এ Commit করবে না।
- নতুন Database Model Field যোগ করলে শুধু `create_all()`-এর ওপর নির্ভর করবে না; Versioned Alembic Migration তৈরি করবে।
- Production Event-এ ব্যবহারের আগে Backup, Email Deliverability, Load Test ও Access Policy যাচাই করবে।

## ১৪. SDP Viva / Documentation

`docs/` Folder-এ Architecture, Test Plan, Project Report Outline ও বাংলা Viva Guide রয়েছে। এগুলো পড়ে প্রত্যেক Team Member-কে Registration Flow, QR Token, Database Relationship, Email Service এবং Atomic Check-in বুঝতে হবে।
