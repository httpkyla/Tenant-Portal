
TENANT PORTAL (Python/FastAPI Advanced)

What’s included
- User accounts with password (session-based)
- Admin portal: tenants & buildings
- Maintenance, Payments, Deliveries (COD or Paid)
- Downloadable PDF receipts for each action
- Email receipts via Gmail (App Password)
- SQLite database

Quick start (Windows)
1) Unzip to e.g. C:\Users\User\tenant-portal-python-advanced
2) In CMD:
   cd C:\Users\User\tenant-portal-python-advanced
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt

3) Create .env:
   copy .env.example .env
   - Put a long random SECRET_KEY
   - Set ADMIN_EMAIL and ADMIN_PASSWORD
   - Set Gmail SMTP (use App Password)

4) Run:
   uvicorn app:app --reload --port 8000

Open:
- http://localhost:8000           (home)
- http://localhost:8000/login     (log in)
- http://localhost:8000/register  (create tenant account)
- http://localhost:8000/dashboard (tenant dashboard)
- http://localhost:8000/admin     (admin dashboard; log in as admin)

Notes
- Receipts are generated as PDFs and downloadable from /receipt/... and emailed to the user’s address.
- If email fails (wrong SMTP), app still works; check console logs.
- Uploaded photos saved under static/uploads.
- To reset data, delete tenant.db.
