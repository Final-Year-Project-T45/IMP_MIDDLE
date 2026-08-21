import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timezone

from app.database import get_db
from app.schemas.domain import TaskCreateRequest
from app.models.task_record import TaskRecord
from app.models.audit_event import AuditEvent
from app.agents.graph import finsecure_workflow
import logging

logger = logging.getLogger("finsecure.api.tasks")

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

def execute_task_workflow(task_id: str, request_text: str, user_id: str, db: Session):
    initial_state = {
        "task_id": task_id,
        "user_id": user_id,
        "original_request": request_text,
        "task_category": "UNKNOWN",
        "status": "PENDING",
        "plan": [],
        "context": {},
        "execution_request": {},
        "execution_output": {},
        "audit_result": {},
        "final_result": "",
        "errors": [],
        "timestamps": {},
        "agent_history": [],
        "audit_trail": [],
        "tool_call_log": [],          # Observability: all LLM tool calls across all agents
        "security_context": None,
        "trust_score": 1.0,
        "provenance_chain": []
    }

    # Execute LangGraph Workflow
    final_state = finsecure_workflow.invoke(initial_state)

    # Persist to DB
    task_rec = db.query(TaskRecord).filter(TaskRecord.task_id == task_id).first()
    if task_rec:
        task_rec.task_type = final_state.get("task_category", "UNKNOWN")
        task_rec.status = final_state.get("status", "COMPLETED")
        task_rec.plan_json = json.dumps(final_state.get("plan", []))
        task_rec.context_json = json.dumps(final_state.get("context", {}))
        task_rec.execution_json = json.dumps(final_state.get("execution_output", {}))
        task_rec.audit_json = json.dumps(final_state.get("audit_result", {}))
        task_rec.final_result = final_state.get("final_result", "")
        task_rec.completed_at = datetime.now(timezone.utc)
        
        # Save Audit Trail Hops to DB
        audit_hops = final_state.get("audit_trail", [])
        for hop in audit_hops:
            ev = AuditEvent(
                task_id=task_id,
                source_agent=hop.get("source_agent", "UNKNOWN"),
                destination_agent=hop.get("destination_agent", "UNKNOWN"),
                event_type=hop.get("event_type", "INTER_AGENT_MESSAGE"),
                action_summary=hop.get("action_summary", ""),
                status=hop.get("status", "PASS")
            )
            db.add(ev)

        db.commit()

    return final_state

@router.post("/execute")
def create_and_execute_task(payload: TaskCreateRequest, db: Session = Depends(get_db)):
    """
    Submits a natural language banking request, executes the 5-Agent LangGraph workflow,
    and returns complete execution details and audit trail.
    """
    import uuid
    task_id = f"TASK-{uuid.uuid4().hex[:8].upper()}"
    
    # Create initial pending task record
    task_rec = TaskRecord(
        task_id=task_id,
        user_id=payload.user_id,
        request=payload.request,
        task_type="PENDING",
        status="RUNNING"
    )
    db.add(task_rec)
    db.commit()

    # Execute workflow synchronously for API response
    final_state = execute_task_workflow(task_id, payload.request, payload.user_id, db)
    
    task_status = final_state.get("status", "COMPLETED")
    exec_out = final_state.get("execution_output", {})
    audit = final_state.get("audit_result", {})
    is_failed = task_status == "FAILED" or exec_out.get("status") in {"FAILED", "ERROR"} or audit.get("audit_status") == "FAILED"
    is_inconclusive = task_status == "INCONCLUSIVE" or audit.get("audit_status") == "INCONCLUSIVE"
    if is_failed:
        overall_status = "FAILED"
    elif is_inconclusive:
        overall_status = "INCONCLUSIVE"
    else:
        overall_status = "SUCCESS"

    resp = {
        "status": overall_status,
        "task_id": task_id,
        "task_category": final_state.get("task_category"),
        "task_status": task_status,
        "plan": final_state.get("plan"),
        "context": final_state.get("context"),
        "execution_output": final_state.get("execution_output"),
        "audit_result": final_state.get("audit_result"),
        "final_result": final_state.get("final_result"),
        "agent_history": final_state.get("agent_history"),
        "tool_call_log": final_state.get("tool_call_log", []),
        "audit_trail": final_state.get("audit_trail"),
        "llm_telemetry": final_state.get("llm_telemetry", {})
    }

    if is_failed or is_inconclusive:
        resp["failure_stage"] = final_state.get("failure_stage") or ("Executor" if exec_out.get("status") == "FAILED" else ("Auditor" if audit.get("audit_status") == "FAILED" else "Researcher"))
        resp["error_type"] = exec_out.get("error_type") or exec_out.get("error") or audit.get("audit_status") or "EXECUTION_FAILED"
        resp["message"] = exec_out.get("error") or exec_out.get("message") or audit.get("summary") or "Task execution failed"

    return resp

@router.get("")
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(TaskRecord).order_by(TaskRecord.created_at.desc()).all()
    res = []
    for t in tasks:
        res.append({
            "task_id": t.task_id,
            "user_id": t.user_id,
            "request": t.request,
            "task_type": t.task_type,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            "final_result": t.final_result
        })
    return res

@router.get("/{task_id}")
def get_task_details(task_id: str, db: Session = Depends(get_db)):
    t = db.query(TaskRecord).filter(TaskRecord.task_id == task_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
        
    audit_events = db.query(AuditEvent).filter(AuditEvent.task_id == task_id).order_by(AuditEvent.timestamp.asc()).all()
    
    return {
        "task_id": t.task_id,
        "user_id": t.user_id,
        "request": t.request,
        "task_type": t.task_type,
        "status": t.status,
        "plan": json.loads(t.plan_json) if t.plan_json else [],
        "context": json.loads(t.context_json) if t.context_json else {},
        "execution_output": json.loads(t.execution_json) if t.execution_json else {},
        "audit_result": json.loads(t.audit_json) if t.audit_json else {},
        "final_result": t.final_result,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        "audit_events": [
            {
                "event_id": ev.event_id,
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                "source_agent": ev.source_agent,
                "destination_agent": ev.destination_agent,
                "event_type": ev.event_type,
                "action_summary": ev.action_summary,
                "status": ev.status
            } for ev in audit_events
        ]
    }
