from sqlalchemy import Column, String, DateTime, Text
from datetime import datetime, timezone
from app.database import Base

class TaskRecord(Base):
    __tablename__ = "tasks"

    task_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, default="EMP-1092")
    request = Column(Text, nullable=False)
    task_type = Column(String, default="UNKNOWN") # ACCOUNT_INQUIRY, POLICY_LOOKUP, FUND_TRANSFER, ACCOUNT_FREEZE, FRAUD_CASE_LOOKUP, LOAN_DISBURSEMENT
    status = Column(String, default="PENDING") # PENDING, RUNNING, COMPLETED, FAILED
    plan_json = Column(Text, nullable=True)
    context_json = Column(Text, nullable=True)
    execution_json = Column(Text, nullable=True)
    audit_json = Column(Text, nullable=True)
    final_result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
