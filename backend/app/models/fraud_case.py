from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class FraudCase(Base):
    __tablename__ = "fraud_cases"

    case_id = Column(String, primary_key=True, index=True) # e.g. FC-2291
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=False, index=True)
    account_id = Column(String, nullable=False, index=True)
    case_type = Column(String, default="SUSPICIOUS_ACTIVITY") # SUSPICIOUS_ACTIVITY, COMPROMISED_CREDENTIALS, ACCOUNT_TAKEOVER
    severity = Column(String, default="HIGH") # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String, default="OPEN") # OPEN, UNDER_INVESTIGATION, RESOLVED, CLOSED
    description = Column(String, nullable=False)
    assigned_analyst = Column(String, default="ANALYST_SARAH_JENKINS")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    customer = relationship("Customer", back_populates="fraud_cases")
