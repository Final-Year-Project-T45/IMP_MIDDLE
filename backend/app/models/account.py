from sqlalchemy import Column, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class Account(Base):
    __tablename__ = "accounts"

    account_id = Column(String, primary_key=True, index=True) # e.g. 4821, ACC-4821
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=False, index=True)
    account_type = Column(String, default="RETAIL") # RETAIL, CORPORATE, SAVINGS
    balance = Column(Float, nullable=False, default=0.0)
    status = Column(String, default="ACTIVE") # ACTIVE, FROZEN, CLOSED
    daily_transfer_limit = Column(Float, default=200000.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    customer = relationship("Customer", back_populates="accounts")
