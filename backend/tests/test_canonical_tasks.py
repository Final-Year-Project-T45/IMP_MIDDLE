import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add parent app path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import SessionLocal
from app.models.account import Account
from app.models.loan import Loan

client = TestClient(app)

def test_database_seeded_properly():
    db = SessionLocal()
    try:
        a4821 = db.query(Account).filter(Account.account_id == "ACC-4821").first()
        a9034 = db.query(Account).filter(Account.account_id == "ACC-9034").first()
        a7742 = db.query(Account).filter(Account.account_id == "ACC-7742").first()
        loan = db.query(Loan).filter(Loan.loan_id == "LOAN-6634").first()

        assert a4821 is not None, "Account 4821 must exist"
        assert a9034 is not None, "Account 9034 must exist"
        assert a7742 is not None, "Account 7742 must exist"
        assert loan is not None, "Loan LOAN-6634 must exist"
        assert loan.amount == 500000.0
    finally:
        db.close()

def test_canonical_task_1_account_inquiry():
    response = client.post("/api/tasks/execute", json={
        "request": "What's the current balance and last 5 transactions for account ending 4821?",
        "user_id": "EMP-1092"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["task_category"] == "ACCOUNT_INQUIRY"
    assert "4821" in data["final_result"] or "125,000" in data["final_result"]

def test_canonical_task_2_policy_lookup():
    response = client.post("/api/tasks/execute", json={
        "request": "Summarize our policy on wire transfer limits for retail customers.",
        "user_id": "EMP-1092"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["task_category"] == "POLICY_LOOKUP"
    assert "Policy" in data["final_result"] or "transfer limit" in data["final_result"].lower()

def test_canonical_task_3_fund_transfer():
    # Initial balance of 4821 is 125,000; 9034 is 45,000
    response = client.post("/api/tasks/execute", json={
        "request": "Approve a fund transfer of ₹85,000 from account 4821 to account 9034.",
        "user_id": "EMP-1092"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["task_category"] == "FUND_TRANSFER"
    
    # DB Balance Verification
    db = SessionLocal()
    try:
        a4821 = db.query(Account).filter(Account.account_id == "ACC-4821").first()
        a9034 = db.query(Account).filter(Account.account_id == "ACC-9034").first()
        assert a4821.balance == 125000.0 - 85000.0 # 40,000
        assert a9034.balance == 45000.0 + 85000.0  # 130,000
    finally:
        db.close()

def test_canonical_task_4_account_freeze():
    response = client.post("/api/tasks/execute", json={
        "request": "Freeze account 7742 — customer reported it as compromised.",
        "user_id": "EMP-1092"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["task_category"] == "ACCOUNT_FREEZE"
    
    # DB Status Verification
    db = SessionLocal()
    try:
        a7742 = db.query(Account).filter(Account.account_id == "ACC-7742").first()
        assert a7742.status == "FROZEN"
    finally:
        db.close()

def test_canonical_task_5_fraud_case_lookup():
    response = client.post("/api/tasks/execute", json={
        "request": "Pull up the status of fraud case #FC-2291.",
        "user_id": "EMP-1092"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["task_category"] == "FRAUD_CASE_LOOKUP"
    assert "FC-2291" in data["final_result"]

def test_canonical_task_6_loan_disbursement():
    response = client.post("/api/tasks/execute", json={
        "request": "Disburse the approved personal loan of ₹5,00,000 for customer ID C-6634.",
        "user_id": "EMP-1092"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["task_category"] == "LOAN_DISBURSEMENT"
    
    # DB Loan Status Verification
    db = SessionLocal()
    try:
        loan = db.query(Loan).filter(Loan.loan_id == "LOAN-6634").first()
        assert loan.disbursement_status == "DISBURSED"
    finally:
        db.close()
