
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

def make_pdf_receipt(title: str, fields: dict) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 2*cm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, y, title)
    y -= 1.2*cm
    c.setFont("Helvetica", 11)
    for k, v in fields.items():
        text = f"{k}: {v}"
        c.drawString(2*cm, y, text[:110])  # simple clipping
        y -= 0.8*cm
        if y < 2*cm:
            c.showPage()
            y = height - 2*cm
            c.setFont("Helvetica", 11)
    c.showPage()
    c.save()
    return buf.getvalue()
