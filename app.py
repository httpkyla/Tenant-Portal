from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import MaintenanceRequest

# create db tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("base.html", {"request": request, "title": "Home"})


@app.get("/maintenance/form")
def show_form(request: Request):
    return templates.TemplateResponse("maintenance_form.html", {"request": request})


@app.post("/maintenance")
def create_request(
    tenant_name: str = Form(...),
    unit_number: str = Form(...),
    property_name: str = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    new_req = MaintenanceRequest(
        tenant_name=tenant_name,
        unit_number=unit_number,
        property_name=property_name,
        description=description,
        status="Pending"
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    return RedirectResponse(url="/maintenance/list", status_code=303)


@app.get("/maintenance/list")
def list_requests(request: Request, db: Session = Depends(get_db)):
    requests = db.query(MaintenanceRequest).order_by(MaintenanceRequest.created_at.desc()).all()
    return templates.TemplateResponse("list.html", {"request": request, "requests": requests})
