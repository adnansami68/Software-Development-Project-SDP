# SDP Report Outline — EventPass

## Project title
Smart Event Registration, QR Ticketing & Entry Validation System

## Abstract
EventPass is a Python-based web application designed to automate participant registration, QR ticket issuance and event entry validation. Organizers can create multiple events, review participant applications and approve registrations. Upon approval, the system generates a unique QR ticket as a PDF and sends it to the participant by email. At the event gate, the QR code is scanned and validated against the central database. The system blocks duplicate check-ins and records gate activity for reporting.

## 1. Introduction
Describe the common challenges of manual event registration and gate entry: long queues, manual list lookup, difficulty tracking attendance and risk of duplicate ticket use. Explain the need for a centralized registration and check-in workflow.

## 2. Problem Statement
Manual event check-in can consume time and can make duplicate or invalid entry attempts difficult to detect. Organizers may also maintain participant lists, email confirmations and attendance records separately. EventPass combines these activities in one application.

## 3. Objectives
- Develop a multi-event registration platform.
- Allow organizers to approve or reject participant registrations.
- Generate a unique QR ticket for each approved participant.
- Send ticket PDFs through email.
- Validate entry tickets using a webcam or mobile browser camera.
- Prevent duplicate entry using database-level checks.
- Record and export attendance and gate logs.

## 4. Scope and Limitations
The current project is an SDP prototype for small and medium-sized event workflows. It uses SQLite for local development and PostgreSQL (Neon) for Vercel production. Production deployments require HTTPS and a shared persistent database. QR tickets are bearer credentials; for high-security events, gate staff should verify participant identity in addition to scanning the QR.

## 5. Methodology
1. Organizer creates an event.
2. Organizer publishes the event.
3. Participant submits the registration form.
4. The system validates required fields and creates a pending registration.
5. Organizer approves the registration.
6. The system creates a random ticket token, stores its SHA-256 hash, generates a QR code and creates a PDF ticket.
7. The mail service sends the ticket PDF.
8. Gate staff open check-in and scan the QR code.
9. The server checks event match, token hash, approval status and previous check-in state.
10. A conditional database update records the first successful entry; subsequent attempts are rejected and logged.
11. Organizer reviews the check-in log and exports a CSV report.

## 6. Tools and Technologies
Python, Flask, Flask-Login, Flask-SQLAlchemy, SQLite (local development), PostgreSQL / Neon (production), HTML, CSS, JavaScript, html5-qrcode, qrcode, Pillow, ReportLab and SMTP.

## 7. Database Design
Include an ER diagram for `users`, `events`, `registrations` and `checkin_logs`. Explain primary keys, foreign keys, event-scoped email/student ID uniqueness and the unique ticket token hash.

## 8. Implementation
Explain the application factory, blueprints, models, ticket service, email service, scanner JavaScript and one-time validation service. Add screenshots from the actual running application.

## 9. Testing and Results
Use the test plan in `TEST_PLAN.md`. Include screenshots/results for a successful registration, pending state, organizer approval, PDF ticket, valid scan, duplicate scan, invalid scan, closed gate and CSV export. Report measured test results rather than inventing numbers.

## 10. Conclusion and Future Work
Conclude that EventPass demonstrates a complete registration-to-entry workflow. Future enhancements may include PostgreSQL deployment, online payment, email verification, role-based gate staff accounts, event check-in windows, offline-first scanning with secure synchronization and attendee identity verification.
