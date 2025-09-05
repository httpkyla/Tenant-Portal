from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from database import Base   # whatever file your Base = declarative_base() is in

class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    id = Column(Integer, primary_key=True, index=True)

    tenant_name   = Column(String(100), nullable=False)
    unit_number   = Column(String(20), nullable=False)

    # Store which building they belong to (eg. "Macy Mansion")
    property_name = Column(String(100), nullable=False)

    description   = Column(Text, nullable=False)

    status        = Column(String(20), default="Pending")  # Pending / In Progress / Completed

    created_at    = Column(DateTime, default=datetime.utcnow)
