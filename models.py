
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Text, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from database import Base

class Building(Base):
    __tablename__ = "buildings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tenants = relationship("User", back_populates="building")

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="tenant")  # 'tenant' or 'admin'
    building_id: Mapped[int | None] = mapped_column(ForeignKey("buildings.id"), nullable=True)
    building = relationship("Building", back_populates="tenants")

class Maintenance(Base):
    __tablename__ = "maintenance"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    note: Mapped[str] = mapped_column(Text)
    photo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="Pending")  # Pending -> In Progress -> Completed
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    description: Mapped[str] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Float)
    due_date: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="Unpaid")
    paid_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Delivery(Base):
    __tablename__ = "deliveries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    courier: Mapped[str] = mapped_column(String(64))
    tracking: Mapped[str] = mapped_column(String(128))
    is_cod: Mapped[bool] = mapped_column(Boolean, default=False)
    cod_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    cod_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(16), default="Logged") # Logged -> Received
    received_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
