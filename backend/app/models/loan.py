from sqlalchemy import Column, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class Loan(Base):
    __tablename__ = "loans"

    loan_id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=False, index=True)
    loan_type = Column(String, default="PERSONAL") # PERSONAL, HOME, CAR
    amount = Column(Float, nullable=False)
    approval_status = Column(String, default="APPROVED") # APPROVED, PENDING, REJECTED
    disbursement_status = Column(String, default="PENDING") # PENDING, DISBURSED
    approved_by = Column(String, default="CREDIT_COMMITTEE")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    disbursed_at = Column(DateTime, nullable=True)

    customer = relationship("Customer", back_populates="loans")
