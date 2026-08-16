from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    customer_type = Column(String, default="RETAIL") # RETAIL, CORPORATE, PREMIUM
    kyc_status = Column(String, default="VERIFIED") # VERIFIED, PENDING, EXPIRED
    risk_level = Column(String, default="LOW") # LOW, MEDIUM, HIGH
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    accounts = relationship("Account", back_populates="customer")
    loans = relationship("Loan", back_populates="customer")
    fraud_cases = relationship("FraudCase", back_populates="customer")
