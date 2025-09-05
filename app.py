@app.post("/maintenance")
async def create_request(
    request: Request,
    tenant_name: str = Form(...),
    unit_number: str = Form(...),
    property_name: str = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    new_request = MaintenanceRequest(
        tenant_name=tenant_name,
        unit_number=unit_number,
        property_name=property_name,
        description=description
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return RedirectResponse(url="/maintenance", status_code=303)
