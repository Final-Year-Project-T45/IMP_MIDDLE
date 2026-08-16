from sqlalchemy import Column, String, Float, DateTime
from datetime import datetime, timezone
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String, primary_key=True, index=True)
    sender_account = Column(String, nullable=False, index=True)
    receiver_account = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, default="WIRE_TRANSFER") # WIRE_TRANSFER, DEPOSIT, LOAN_DISBURSEMENT
    status = Column(String, default="SUCCESS") # SUCCESS, FAILED, PENDING
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    initiated_by = Column(String, default="SYSTEM")
    description = Column(String, nullable=True)
