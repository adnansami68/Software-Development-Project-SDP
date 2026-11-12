# EventPass — Production Deployment Checklist (বাংলা)

## A. Local
- [ ] Python 3.12+ / Python 3.14 available
- [ ] `setup_windows.bat` সফল
- [ ] `create_admin.bat` দিয়ে local organizer তৈরি
- [ ] `run_windows.bat` দিয়ে local site চালু
- [ ] Registration → Pending → Approve → PDF → QR scan → duplicate scan পরীক্ষা
- [ ] `test_windows.bat` বা `python manage.py test` সফল

## B. Database (Neon PostgreSQL)
- [ ] Neon project তৈরি
- [ ] Local `.env.production` তৈরি (Git ignored)
- [ ] Direct Neon URL দিয়ে `python manage.py --env-file .env.production init-db`
- [ ] একই DB-তে `python manage.py --env-file .env.production create-admin`
- [ ] Admin credential নিরাপদে সংরক্ষণ
- [ ] Runtime URL-এর জন্য pooled connection (`-pooler`) বেছে নেওয়া

## C. GitHub
- [ ] `.env`, `.env.production`, `.venv`, `instance/` Git status-এ নেই
- [ ] `.gitignore` আছে
- [ ] README ও docs আছে
- [ ] `git status --short` যাচাই
- [ ] Commit ও push `main`

## D. Vercel
- [ ] GitHub repository Import
- [ ] Root directory repository root
- [ ] Flask auto-detection / `app.py` entry point
- [ ] `SECRET_KEY` set
- [ ] `DATABASE_URL` = pooled PostgreSQL URL
- [ ] `APP_BASE_URL` = deployed HTTPS URL
- [ ] `TIMEZONE=Asia/Dhaka`
- [ ] `AUTO_CREATE_DB=false` (schema আগে initialize করা হয়েছে)
- [ ] `SESSION_COOKIE_SECURE=true`
- [ ] SMTP environment variables set
- [ ] Production deploy complete
- [ ] `/health` returns database connected
- [ ] Admin login works
- [ ] Public registration link works
- [ ] Approval email + PDF works
- [ ] HTTPS camera scan works
- [ ] Duplicate scan rejected

## E. Before a real event
- [ ] Multiple devices/gates test on same database
- [ ] Email provider sender/domain verified
- [ ] Database backup plan decided
- [ ] Gate operator account and permission plan decided
- [ ] QR code sharing risk understood; ID check policy decided
- [ ] Registration capacity and event dates verified
- [ ] Attendee data access limited to authorized organizers
