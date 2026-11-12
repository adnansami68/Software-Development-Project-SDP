# EventPass — SDP Viva Guide (বাংলা + English)

## ১. Project Introduction

**Project Title:** Smart Event Registration, QR Ticketing & Entry Validation System.

**বাংলায়:** এটি একটি Python Flask ভিত্তিক Web Application। এর মাধ্যমে একাধিক Event তৈরি করা যায়, Participant অনলাইনে Registration করতে পারে, Organizer Registration Approve করলে Unique QR Ticket PDF তৈরি হয় এবং Email-এ পাঠানো হয়। Event-এর Gate-এ QR Scan করলে Server Ticket Valid কি না যাচাই করে এবং সফল Entry একবারই গ্রহণ করে।

**Problem statement:** Manual participant list checking takes time, creates queues and makes duplicate or unauthorized entry harder to detect. EventPass digitizes registration, ticket issuance and gate validation.

## ২. পাঁচজনের মধ্যে কাজ ভাগ

1. **Member 1 — Backend / Flask:** routes, request/response, organizer login.
2. **Member 2 — Event & Registration:** event setup, public registration, form validation.
3. **Member 3 — QR & Email:** random token, QR generation, PDF pass and SMTP.
4. **Member 4 — Check-in & Security:** scan validation, duplicate prevention, event/gate validation.
5. **Member 5 — Database & UI:** SQLAlchemy models, dashboard, reports and testing integration.

সবাইকে পুরো flow, database relationship এবং ticket validation বুঝতে হবে।

## ৩. Common Viva Questions

### Q1. What is the main objective of this project?
**Answer:** To automate event registration, QR ticket generation, participant approval and secure one-time entry validation.

### Q2. Why did you choose Python?
**Answer:** Python has readable syntax and a large ecosystem. Flask, SQLAlchemy, qrcode and ReportLab allow us to implement the system with a manageable codebase.

### Q3. What is Flask?
**Answer:** Flask is a lightweight Python web framework. It handles URL routes, HTTP requests, templates and application responses.

### Q4. What is a QR Code?
**Answer:** A QR Code is a two-dimensional barcode that can store data and be read by a camera or scanner.

### Q5. What information is stored in the QR?
**Answer:** A version prefix, event slug and a randomly generated secret token. It does not store the participant's email or phone number.

### Q6. Why do you use a random token?
**Answer:** A random token is difficult to guess. It works as a ticket credential and does not expose a predictable Student ID.

### Q7. Why is the token hash stored in the database?
**Answer:** Storing only a SHA-256 digest means the database does not keep the original QR secret in plain text. During scanning, the server hashes the received token and compares the digest.

### Q8. What is SQLite?
**Answer:** SQLite is a lightweight relational database stored in a file and is used for local development. For the Vercel-hosted production version, EventPass uses PostgreSQL (Neon) because a serverless deployment needs a persistent shared database.

### Q9. What is SQLAlchemy?
**Answer:** SQLAlchemy is an ORM and database toolkit. It lets Python code work with database tables through model classes and query expressions.

### Q10. What is CRUD?
**Answer:** CRUD means Create, Read, Update and Delete. Our system creates events and registrations, reads records, updates approvals and check-in data, and supports event management operations.

### Q11. How does duplicate-entry prevention work?
**Answer:** The server performs a conditional database update. It only writes the check-in time if the ticket is approved and `checked_in_at` is still NULL. After the first successful update, another scan cannot update the same row and is marked duplicate.

### Q12. What if a ticket is scanned at another event?
**Answer:** The QR includes an event slug. The server compares it with the event being scanned. A mismatch is rejected.

### Q13. What happens if an organizer reissues a ticket?
**Answer:** A new random token and hash are generated. The old token hash is replaced, so the previous QR is no longer valid.

### Q14. Why do you need SMTP?
**Answer:** SMTP is a protocol used to send emails. We use Python's `smtplib` to email an approved participant's PDF ticket.

### Q15. Does the system work without internet?
**Answer:** The local Flask app and SQLite database can work offline after dependencies are installed. Automated email needs internet and SMTP. Browser camera access works on localhost; mobile camera access over a network generally requires HTTPS. The browser scanner script must also be available.

### Q16. Can a participant share a QR ticket?
**Answer:** Yes, a QR is a bearer credential. The first person who presents it may use it. For important events, the gate team should compare the participant's name or ID with an identity document. A future enhancement can add a stronger identity check.

### Q17. What are the limitations?
**Answer:** The current release is an SDP-scale prototype. Local development uses SQLite, while the Vercel production setup uses PostgreSQL. Before a real high-volume event, add load testing, backups, rate limiting, operational monitoring and stronger gate identity procedures. QR sharing cannot be fully prevented by QR validation alone.

### Q18. What future improvements can be added?
**Answer:** Online payment, attendee self-service ticket retrieval, email verification, event-specific roles, multi-language UI, PostgreSQL, rate limiting, audit exports and stronger identity verification.

## ৪. Demo order for the viva board

1. Organizer logs in.
2. Create a new event and publish it.
3. Open its public registration URL in another browser/incognito window.
4. Submit a participant registration.
5. Return to organizer workspace and approve the participant.
6. Show the created PDF ticket and the email (or local email preview if SMTP is not configured).
7. Open the scanner and open the gate.
8. Scan the QR from the PDF on a phone screen or show the QR on another screen.
9. Show `VALID` on the first scan.
10. Scan the same QR again and show `DUPLICATE`.
11. Show invalid/wrong-event behavior and the check-in log.
12. Export the CSV report.

## ৫. Viva preparation rule

প্রত্যেক সদস্য নিজের Module-এর জন্য এই ৪টি বিষয় ব্যাখ্যা করতে পারবে:

- Input কী?
- Processing কীভাবে হয়?
- Output কী?
- Error বা invalid condition হলে কী হয়?

শুধু Code মুখস্থ না করে একটি sample registration থেকে successful scan পর্যন্ত data কীভাবে database table-এ যায়, তা হাতে এঁকে বুঝতে অনুশীলন করবে।
