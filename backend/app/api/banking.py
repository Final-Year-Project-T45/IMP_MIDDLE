from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.database import get_db
from app.services.banking_service import BankingService
from app.models.account import Account
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.models.loan import Loan
from app.schemas.domain import TransferRequest, FreezeAccountRequest, DisburseLoanRequest

router = APIRouter(prefix="/api/banking", tags=["Banking"])

@router.get("/accounts")
def list_accounts(db: Session = Depends(get_db)):
    accounts = db.query(Account).all()
    res = []
    for a in accounts:
        cust = db.query(Customer).filter(Customer.customer_id == a.customer_id).first()
        res.append({
            "account_id": a.account_id,
            "customer_id": a.customer_id,
            "customer_name": cust.name if cust else "Unknown",
            "account_type": a.account_type,
            "balance": a.balance,
            "status": a.status,
            "daily_transfer_limit": a.daily_transfer_limit,
            "risk_level": cust.risk_level if cust else "LOW"
        })
    return res

@router.get("/accounts/{account_id}")
def get_account_details(account_id: str, db: Session = Depends(get_db)):
    acc = BankingService.get_account(db, account_id)
    if acc.get("status") == "ERROR":
        raise HTTPException(status_code=404, detail=acc.get("message"))
    txs = BankingService.get_transactions(db, account_id, limit=10)
    acc["recent_transactions"] = txs.get("transactions", [])
    return acc

@router.post("/accounts/{account_id}/freeze")
def freeze_account_endpoint(account_id: str, payload: Optional[FreezeAccountRequest] = None, db: Session = Depends(get_db)):
    reason = payload.reason if payload else "Manual operational freeze"
    res = BankingService.freeze_account(db, account_id, reason=reason)
    if res.get("status") == "FAILED":
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.post("/accounts/{account_id}/unfreeze")
def unfreeze_account_endpoint(account_id: str, db: Session = Depends(get_db)):
    res = BankingService.unfreeze_account(db, account_id, reason="Manual unfreeze verification")
    if res.get("status") == "FAILED":
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.get("/transactions")
def list_transactions(db: Session = Depends(get_db)):
    txs = db.query(Transaction).order_by(Transaction.timestamp.desc()).all()
    res = []
    for t in txs:
        res.append({
            "transaction_id": t.transaction_id,
            "sender_account": t.sender_account,
            "receiver_account": t.receiver_account,
            "amount": t.amount,
            "transaction_type": t.transaction_type,
            "status": t.status,
            "timestamp": t.timestamp.isoformat() if t.timestamp else None,
            "initiated_by": t.initiated_by,
            "description": t.description
        })
    return res

@router.post("/transfers")
def execute_direct_transfer(payload: TransferRequest, db: Session = Depends(get_db)):
    res = BankingService.transfer_funds(
        db=db,
        sender_account=payload.sender_account,
        receiver_account=payload.receiver_account,
        amount=payload.amount,
        description=payload.description
    )
    if res.get("status") == "FAILED":
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.get("/loans")
def list_loans(db: Session = Depends(get_db)):
    loans = db.query(Loan).all()
    res = []
    for l in loans:
        cust = db.query(Customer).filter(Customer.customer_id == l.customer_id).first()
        res.append({
            "loan_id": l.loan_id,
            "customer_id": l.customer_id,
            "customer_name": cust.name if cust else "Unknown",
            "loan_type": l.loan_type,
            "amount": l.amount,
            "approval_status": l.approval_status,
            "disbursement_status": l.disbursement_status,
            "approved_by": l.approved_by,
            "created_at": l.created_at.isoformat() if l.created_at else None,
            "disbursed_at": l.disbursed_at.isoformat() if l.disbursed_at else None
        })
    return res

@router.post("/loans/{loan_id}/disburse")
def disburse_loan_endpoint(loan_id: str, db: Session = Depends(get_db)):
    res = BankingService.disburse_loan(db, loan_id)
    if res.get("status") == "FAILED":
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res
