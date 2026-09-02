from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.fraud_case import FraudCase
from app.models.customer import Customer
from app.models.account import Account

VALID_FRAUD_STATUSES = {"OPEN", "UNDER_INVESTIGATION", "RESOLVED", "CLOSED"}
VALID_FRAUD_TRANSITIONS = {
    "OPEN": {"UNDER_INVESTIGATION", "CLOSED"},
    "UNDER_INVESTIGATION": {"RESOLVED", "CLOSED"},
    "RESOLVED": {"CLOSED", "UNDER_INVESTIGATION"},
    "CLOSED": {"UNDER_INVESTIGATION"}
}

class FraudService:
    @staticmethod
    def get_fraud_case(db: Session, case_id: str) -> Dict[str, Any]:
        # Handle FC-2291 or 2291
        fc = db.query(FraudCase).filter(FraudCase.case_id == case_id).first()
        if not fc:
            fc = db.query(FraudCase).filter(FraudCase.case_id.endswith(case_id)).first()

        if not fc:
            return {"status": "ERROR", "case_id": case_id, "message": f"Fraud case '{case_id}' not found."}

        cust = db.query(Customer).filter(Customer.customer_id == fc.customer_id).first()
        acc = db.query(Account).filter(Account.account_id == fc.account_id).first()

        return {
            "status": "SUCCESS",
            "case_id": fc.case_id,
            "customer_id": fc.customer_id,
            "customer_name": cust.name if cust else "Unknown",
            "account_id": fc.account_id,
            "account_status": acc.status if acc else "Unknown",
            "case_type": fc.case_type,
            "severity": fc.severity,
            "case_status": fc.status,
            "description": fc.description,
            "assigned_analyst": fc.assigned_analyst,
            "created_at": fc.created_at.isoformat() if fc.created_at else None
        }

    @staticmethod
    def update_fraud_case(db: Session, case_id: str, new_status: str, notes: str = "") -> Dict[str, Any]:
        res = FraudService.get_fraud_case(db, case_id)
        if res.get("status") == "ERROR":
            return {"status": "FAILED", "error": res.get("message")}

        normalized_status = (new_status or "").strip().upper()
        if normalized_status not in VALID_FRAUD_STATUSES:
            return {
                "status": "FAILED",
                "error": f"Invalid fraud case status '{new_status}'. Allowed statuses: {sorted(list(VALID_FRAUD_STATUSES))}."
            }

        fc = db.query(FraudCase).filter(FraudCase.case_id == res["case_id"]).first()
        current_status = fc.status

        # If already in the target status, handle predictably
        if normalized_status == current_status:
            return {
                "status": "SUCCESS",
                "case_id": fc.case_id,
                "previous_status": current_status,
                "updated_status": current_status,
                "message": f"Fraud case '{fc.case_id}' was already in status '{current_status}'."
            }

        # Check valid state transitions
        allowed_transitions = VALID_FRAUD_TRANSITIONS.get(current_status, set())
        if normalized_status not in allowed_transitions:
            return {
                "status": "FAILED",
                "error": f"Invalid status transition from '{current_status}' to '{normalized_status}'. Allowed transitions: {sorted(list(allowed_transitions))}."
            }

        prev_status = fc.status
        fc.status = normalized_status
        if notes:
            fc.description += f" [Updated: {notes}]"

        try:
            db.commit()
            return {
                "status": "SUCCESS",
                "case_id": fc.case_id,
                "previous_status": prev_status,
                "updated_status": fc.status,
                "message": f"Fraud case '{fc.case_id}' status updated from {prev_status} to {normalized_status}."
            }
        except Exception as e:
            db.rollback()
            return {"status": "FAILED", "error": str(e)}
