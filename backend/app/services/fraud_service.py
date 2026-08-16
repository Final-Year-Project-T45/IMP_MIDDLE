from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.fraud_case import FraudCase
from app.models.customer import Customer
from app.models.account import Account

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
            return res

        fc = db.query(FraudCase).filter(FraudCase.case_id == res["case_id"]).first()
        fc.status = new_status
        if notes:
            fc.description += f" [Updated: {notes}]"

        try:
            db.commit()
            return {
                "status": "SUCCESS",
                "case_id": fc.case_id,
                "updated_status": fc.status,
                "message": f"Fraud case '{fc.case_id}' status updated to {new_status}."
            }
        except Exception as e:
            db.rollback()
            return {"status": "FAILED", "error": str(e)}
