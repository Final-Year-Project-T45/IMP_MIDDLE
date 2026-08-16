from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.fraud_service import FraudService
from app.models.fraud_case import FraudCase

router = APIRouter(prefix="/api/fraud-cases", tags=["Fraud Cases"])

@router.get("")
def list_fraud_cases(db: Session = Depends(get_db)):
    cases = db.query(FraudCase).all()
    res = []
    for fc in cases:
        details = FraudService.get_fraud_case(db, fc.case_id)
        res.append(details)
    return res

@router.get("/{case_id}")
def get_fraud_case_details(case_id: str, db: Session = Depends(get_db)):
    res = FraudService.get_fraud_case(db, case_id)
    if res.get("status") == "ERROR":
        raise HTTPException(status_code=404, detail=res.get("message"))
    return res
