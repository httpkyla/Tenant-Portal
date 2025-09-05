# app.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database import SessionLocal
from models import MaintenanceRequest, Delivery
from sqlalchemy.orm import Session

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Maintenance form
@app.get("/maintenance", response_class=HTMLResponse)
def maintenance_form(request: Request):
    return templates.TemplateResponse("maintenance.html", {"request": request})

@app.post("/maintenance")
def create_maintenance(
    request: Request,
    tenant_name: str = Form(...),
    unit_number: str = Form(...),
    property_name: str = Form(...),
    description: str = Form(...)
):
    db: Session = SessionLocal()
    req = MaintenanceRequest(
        tenant_name=tenant_name,
        unit_number=unit_number,
        property_name=property_name,
        description=description
    )
    db.add(req)
    db.commit()
    return RedirectResponse("/maintenance", status_code=303)

# Deliveries form
@app.get("/deliveries", response_class=HTMLResponse)
def deliveries_form(request: Request):
    return templates.TemplateResponse("deliveries.html", {"request": request})

@app.post("/deliveries")
def create_delivery(
    request: Request,
    recipient: str = Form(...),
    unit_number: str = Form(...),
    property_name: str = Form(...),
    payment_option: str = Form(...),  # COD or Paid
):
    db: Session = SessionLocal()
    new_delivery = Delivery(
        recipient=recipient,
        unit_number=unit_number,
        property_name=property_name,
        payment_option=payment_option,
    )
    db.add(new_delivery)
    db.commit()
    return RedirectResponse("/deliveries", status_code=303)
