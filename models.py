from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"
    id = Column(Integer, primary_key=True, index=True)
    tenant_name = Column(String, nullable=False)
    unit_number = Column(String, nullable=False)
    property_name = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Delivery(Base):
    __tablename__ = "deliveries"
    id = Column(Integer, primary_key=True, index=True)
    recipient = Column(String, nullable=False)
    unit_number = Column(String, nullable=False)
    property_name = Column(String, nullable=False)
    payment_option = Column(String, nullable=False)  # "COD" or "Paid"
    created_at = Column(DateTime, default=datetime.utcnow)
