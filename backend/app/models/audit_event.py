from sqlalchemy import Column, String, DateTime, Integer
from datetime import datetime, timezone
from app.database import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"

    event_id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    source_agent = Column(String, nullable=False) # Orchestrator, Planner, Researcher, Executor, Auditor
    destination_agent = Column(String, nullable=False)
    event_type = Column(String, default="AGENT_HOP")
    action_summary = Column(String, nullable=False)
    status = Column(String, default="SUCCESS") # SUCCESS, FAILED, WARNING
