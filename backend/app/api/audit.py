from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.audit_event import AuditEvent

router = APIRouter(prefix="/api/audit-events", tags=["Audit Events"])

@router.get("")
def list_audit_events(db: Session = Depends(get_db)):
    events = db.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(100).all()
    res = []
    for ev in events:
        res.append({
            "event_id": ev.event_id,
            "task_id": ev.task_id,
            "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
            "source_agent": ev.source_agent,
            "destination_agent": ev.destination_agent,
            "event_type": ev.event_type,
            "action_summary": ev.action_summary,
            "status": ev.status
        })
    return res
