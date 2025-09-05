
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from dotenv import load_dotenv

from database import Base, engine, get_db
from models import User, Maintenance, Payment, Delivery, Building
from email_utils import send_email
from pdf_utils import make_pdf_receipt

load_dotenv()

app = FastAPI(title="Tenant Portal Advanced")
Base.metadata.create_all(bind=engine)

# static + templates
os.makedirs("static", exist_ok=True)
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# sessions
SECRET_KEY = os.getenv("SECRET_KEY", "changeme")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, same_site="lax")

# bootstrap admin
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

from sqlalchemy import select
from database import SessionLocal

with SessionLocal() as s:
    if ADMIN_EMAIL and ADMIN_PASSWORD:
        existing = s.execute(select(User).where(User.email == ADMIN_EMAIL)).scalar_one_or_none()
        if not existing:
            u = User(email=ADMIN_EMAIL, password_hash=bcrypt.hash(ADMIN_PASSWORD), role="admin")
            s.add(u)
            s.commit()
            print(f"Bootstrapped admin: {ADMIN_EMAIL}")
    else:
        print("No ADMIN_EMAIL/ADMIN_PASSWORD set; admin bootstrap skipped.")

# ----- helpers -----
def get_current_user(request: Request, db: Session) -> Optional[User]:
    uid = request.session.get("user_id")
    if not uid:
        return None
    return db.get(User, uid)

def require_login(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Please log in")
    return user

def require_admin(request: Request, db: Session = Depends(get_db)) -> User:
    user = require_login(request, db)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    return user

def send_receipt_email_safe(to_email: str, title: str, fields: dict, filename: str):
    try:
        pdf = make_pdf_receipt(title, fields)
        body = f"<p>{title}</p><pre>{fields}</pre>"
        return send_email(title, [to_email], body_html=body, attachments=[(filename, pdf, "application/pdf")])
    except Exception as e:
        print("Failed to build/send receipt:", e)
        return False

# ----- routes: auth -----
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("auth/register.html", {"request": request})

@app.post("/register")
def register(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    email = email.strip().lower()
    if db.query(User).filter(User.email==email).first():
        return RedirectResponse("/login?msg=Email%20already%20registered", status_code=303)
    user = User(email=email, password_hash=bcrypt.hash(password), role="tenant")
    db.add(user); db.commit()
    return RedirectResponse("/login?msg=Account%20created%2C%20please%20log%20in", status_code=303)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})

@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    email = email.strip().lower()
    u = db.query(User).filter(User.email==email).first()
    if not u or not bcrypt.verify(password, u.password_hash):
        return RedirectResponse("/login?msg=Invalid%20credentials", status_code=303)
    request.session["user_id"] = u.id
    request.session["role"] = u.role
    return RedirectResponse("/dashboard", status_code=303)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user: User = Depends(require_login)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

# ----- maintenance -----
@app.get("/maintenance", response_class=HTMLResponse)
def maintenance_page(request: Request, db: Session = Depends(get_db), user: User = Depends(require_login)):
    rows = db.query(Maintenance).filter(Maintenance.user_id==user.id).order_by(Maintenance.id.desc()).all()
    return templates.TemplateResponse("maintenance.html", {"request": request, "user": user, "rows": rows})

@app.post("/maintenance")
def maintenance_create(request: Request, note: str = Form(...), photo: UploadFile | None = File(None), db: Session = Depends(get_db), user: User = Depends(require_login)):
    saved_path = None
    if photo and photo.filename:
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{photo.filename.replace(' ', '_')}"
        saved_path = os.path.join("static/uploads", filename)
        with open(saved_path, "wb") as f:
            f.write(photo.file.read())
    m = Maintenance(user_id=user.id, note=note, photo=saved_path, status="Pending")
    db.add(m); db.commit(); db.refresh(m)
    # email receipt
    fields = {"Receipt": "Maintenance", "ID": m.id, "Tenant": user.email, "Note": m.note, "Status": m.status, "Created": m.created_at}
    try:
        import anyio
        anyio.from_thread.run(send_receipt_email_safe, user.email, "Maintenance Receipt", fields, f"maintenance_{m.id}.pdf")
    except Exception as e:
        print("Email schedule failed:", e)
    return RedirectResponse(f"/maintenance?receipt={m.id}", status_code=303)

@app.get("/receipt/maintenance/{mid}.pdf")
def maintenance_receipt_pdf(mid: int, db: Session = Depends(get_db), user: User = Depends(require_login)):
    m = db.get(Maintenance, mid)
    if not m or m.user_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    pdf = make_pdf_receipt("Maintenance Receipt", {
        "ID": m.id, "Tenant": user.email, "Note": m.note, "Status": m.status, "Created": m.created_at
    })
    return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="maintenance_{m.id}.pdf"'} )

# ----- payments -----
@app.get("/payments", response_class=HTMLResponse)
def payments_page(request: Request, db: Session = Depends(get_db), user: User = Depends(require_login)):
    rows = db.query(Payment).filter(Payment.user_id==user.id).order_by(Payment.id.desc()).all()
    return templates.TemplateResponse("payments.html", {"request": request, "user": user, "rows": rows})

@app.post("/payments")
def payments_add(description: str = Form(...), amount: float = Form(...), due_date: str = Form(...), db: Session = Depends(get_db), user: User = Depends(require_login)):
    p = Payment(user_id=user.id, description=description, amount=amount, due_date=due_date, status="Unpaid")
    db.add(p); db.commit(); db.refresh(p)
    # email receipt
    fields = {"Receipt": "Payment", "ID": p.id, "Tenant": user.email, "Description": p.description, "Amount": p.amount, "Due": p.due_date, "Status": p.status}
    try:
        import anyio
        anyio.from_thread.run(send_receipt_email_safe, user.email, "Invoice Created", fields, f"payment_{p.id}.pdf")
    except Exception as e:
        print("Email schedule failed:", e)
    return RedirectResponse(f"/payments?receipt={p.id}", status_code=303)

@app.post("/payments/{pid}/mark-paid")
def payments_mark_paid(pid: int, db: Session = Depends(get_db), user: User = Depends(require_login)):
    p = db.get(Payment, pid)
    if not p or p.user_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    p.status = "Paid"; p.paid_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S"); db.commit()
    # email receipt
    fields = {"Receipt": "Payment", "ID": p.id, "Tenant": user.email, "Description": p.description, "Amount": p.amount, "Status": p.status, "Paid at": p.paid_at}
    try:
        import anyio
        anyio.from_thread.run(send_receipt_email_safe, user.email, "Payment Receipt", fields, f"payment_{p.id}.pdf")
    except Exception as e:
        print("Email schedule failed:", e)
    return RedirectResponse("/payments", status_code=303)

@app.get("/receipt/payment/{pid}.pdf")
def payment_receipt_pdf(pid: int, db: Session = Depends(get_db), user: User = Depends(require_login)):
    p = db.get(Payment, pid)
    if not p or p.user_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    pdf = make_pdf_receipt("Payment Receipt", {
        "ID": p.id, "Tenant": user.email, "Description": p.description, "Amount": p.amount, "Due": p.due_date, "Status": p.status, "Paid at": p.paid_at
    })
    return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="payment_{p.id}.pdf"'} )

# ----- deliveries -----
@app.get("/deliveries", response_class=HTMLResponse)
def deliveries_page(request: Request, db: Session = Depends(get_db), user: User = Depends(require_login)):
    rows = db.query(Delivery).filter(Delivery.user_id==user.id).order_by(Delivery.id.desc()).all()
    return templates.TemplateResponse("deliveries.html", {"request": request, "user": user, "rows": rows})

@app.post("/deliveries")
def deliveries_add(courier: str = Form(...), tracking: str = Form(...), is_cod: bool = Form(False), cod_amount: float | None = Form(None), db: Session = Depends(get_db), user: User = Depends(require_login)):
    d = Delivery(user_id=user.id, courier=courier, tracking=tracking, is_cod=is_cod, cod_amount=cod_amount if is_cod else None, cod_paid=False, status="Logged")
    db.add(d); db.commit(); db.refresh(d)
    # email receipt
    fields = {"Receipt": "Delivery", "ID": d.id, "Tenant": user.email, "Courier": d.courier, "Tracking": d.tracking, "COD?": d.is_cod, "COD Amount": d.cod_amount}
    try:
        import anyio
        anyio.from_thread.run(send_receipt_email_safe, user.email, "Delivery Logged", fields, f"delivery_{d.id}.pdf")
    except Exception as e:
        print("Email schedule failed:", e)
    return RedirectResponse(f"/deliveries?receipt={d.id}", status_code=303)

@app.post("/deliveries/{did}/mark-received")
def deliveries_received(did: int, db: Session = Depends(get_db), user: User = Depends(require_login)):
    d = db.get(Delivery, did)
    if not d or d.user_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    d.status = "Received"; d.received_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.commit()
    return RedirectResponse("/deliveries", status_code=303)

@app.post("/deliveries/{did}/mark-cod-paid")
def deliveries_cod_paid(did: int, db: Session = Depends(get_db), user: User = Depends(require_login)):
    d = db.get(Delivery, did)
    if not d or d.user_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    if not d.is_cod:
        raise HTTPException(status_code=400, detail="Not a COD delivery")
    d.cod_paid = True
    db.commit()
    return RedirectResponse("/deliveries", status_code=303)

@app.get("/receipt/delivery/{did}.pdf")
def delivery_receipt_pdf(did: int, db: Session = Depends(get_db), user: User = Depends(require_login)):
    d = db.get(Delivery, did)
    if not d or d.user_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    pdf = make_pdf_receipt("Delivery Receipt", {
        "ID": d.id, "Tenant": user.email, "Courier": d.courier, "Tracking": d.tracking,
        "COD?": d.is_cod, "COD Amount": d.cod_amount, "COD Paid": d.cod_paid, "Status": d.status, "Received at": d.received_at
    })
    return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="delivery_{d.id}.pdf"'} )

# ----- admin -----
@app.get("/admin", response_class=HTMLResponse)
def admin_index(request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    counts = {
        "tenants": db.query(User).filter(User.role=="tenant").count(),
        "buildings": db.query(Building).count(),
        "maintenance": db.query(Maintenance).count(),
        "payments": db.query(Payment).count(),
        "deliveries": db.query(Delivery).count(),
    }
    return templates.TemplateResponse("admin/index.html", {"request": request, "admin": admin, "counts": counts})

@app.get("/admin/tenants", response_class=HTMLResponse)
def admin_tenants(request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    tenants = db.query(User).filter(User.role=="tenant").all()
    buildings = db.query(Building).all()
    return templates.TemplateResponse("admin/tenants.html", {"request": request, "tenants": tenants, "buildings": buildings})

@app.post("/admin/tenants/{uid}/assign-building")
def admin_assign_building(uid: int, building_id: int = Form(...), db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    u = db.get(User, uid)
    if u and u.role == "tenant":
        u.building_id = building_id or None
        db.commit()
    return RedirectResponse("/admin/tenants", status_code=303)

@app.get("/admin/buildings", response_class=HTMLResponse)
def admin_buildings(request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    buildings = db.query(Building).all()
    return templates.TemplateResponse("admin/buildings.html", {"request": request, "buildings": buildings})

@app.post("/admin/buildings")
def admin_add_building(name: str = Form(...), address: str = Form(""), db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if not name.strip():
        raise HTTPException(status_code=400, detail="Name required")
    if db.query(Building).filter(Building.name==name.strip()).first():
        return RedirectResponse("/admin/buildings?msg=exists", status_code=303)
    b = Building(name=name.strip(), address=address.strip())
    db.add(b); db.commit()
    return RedirectResponse("/admin/buildings", status_code=303)
