"""
Automated Test Suite for FinSecure Phase 1 Banking and Fraud Services.
Covers READ, WRITE, and FAILURE boundary conditions.
"""

import pytest
from app.database import SessionLocal
from app.services.banking_service import BankingService
from app.services.fraud_service import FraudService
from app.services.policy_service import policy_kb
from app.models.account import Account
from app.models.customer import Customer
from app.models.loan import Loan
from app.models.fraud_case import FraudCase


@pytest.fixture
def db():
    session = SessionLocal()
    # Ensure benchmark accounts exist
    sender = session.query(Account).filter(Account.account_id == "ACC-4821").first()
    if not sender:
        sender = Account(
            account_id="ACC-4821",
            customer_id="C-4821",
            account_type="SAVINGS",
            balance=125000.0,
            status="ACTIVE",
            daily_transfer_limit=100000.0
        )
        session.add(sender)

    recv = session.query(Account).filter(Account.account_id == "ACC-9034").first()
    if not recv:
        recv = Account(
            account_id="ACC-9034",
            customer_id="C-9034",
            account_type="SAVINGS",
            balance=45000.0,
            status="ACTIVE",
            daily_transfer_limit=100000.0
        )
        session.add(recv)

    session.commit()
    try:
        yield session
    finally:
        session.close()


# ── READ OPERATIONS ──────────────────────────────────────────────────────────

def test_read_account_inquiry(db):
    res = BankingService.get_account(db, "ACC-4821")
    assert res["status"] == "SUCCESS"
    assert res["account_id"] == "ACC-4821"
    assert "balance" in res
    assert "account_status" in res


def test_read_customer_inquiry(db):
    cust = db.query(Customer).first()
    assert cust is not None, "Customer records must exist"
    res = BankingService.get_customer(db, cust.customer_id)
    assert res["status"] == "SUCCESS"
    assert res["customer_id"] == cust.customer_id
    assert "name" in res
    assert "email" in res


def test_read_transactions_history(db):
    res = BankingService.get_transactions(db, "ACC-4821", limit=5)
    assert res["status"] == "SUCCESS"
    assert "transactions" in res
    assert isinstance(res["transactions"], list)


def test_read_loan_inquiry(db):
    loan = db.query(Loan).first()
    assert loan is not None, "Loan records must exist"
    res = BankingService.get_loan(db, loan.loan_id)
    assert res["status"] == "SUCCESS"
    assert res["loan_id"] == loan.loan_id
    assert "approval_status" in res


def test_read_fraud_case_inquiry(db):
    fc = db.query(FraudCase).first()
    assert fc is not None, "Fraud case records must exist"
    res = FraudService.get_fraud_case(db, fc.case_id)
    assert res["status"] == "SUCCESS"
    assert res["case_id"] == fc.case_id
    assert "case_status" in res


def test_read_policy_lookup():
    res = policy_kb.search("retail transfer limit")
    assert len(res) > 0
    assert any("transfer" in r["content"].lower() for r in res)


# ── WRITE & FAILURE CONDITIONS: FUND TRANSFERS ──────────────────────────────

def test_transfer_funds_successful(db):
    # Setup test account states
    sender = db.query(Account).filter(Account.account_id == "ACC-4821").first()
    receiver = db.query(Account).filter(Account.account_id == "ACC-9034").first()
    sender.status = "ACTIVE"
    receiver.status = "ACTIVE"
    sender.balance = 50000.0
    receiver.balance = 10000.0
    sender.daily_transfer_limit = 100000.0
    db.commit()

    amount = 5000.0
    res = BankingService.transfer_funds(db, "ACC-4821", "ACC-9034", amount)
    assert res["status"] == "SUCCESS"
    assert res["transaction_id"].startswith("TX-")
    assert res["sender_before_balance"] == 50000.0
    assert res["receiver_before_balance"] == 10000.0
    assert res["sender_new_balance"] == 45000.0
    assert res["receiver_new_balance"] == 15000.0

    # Mathematical conservation checks
    assert res["sender_new_balance"] == res["sender_before_balance"] - amount
    assert res["receiver_new_balance"] == res["receiver_before_balance"] + amount


def test_transfer_funds_invalid_amount(db):
    res_zero = BankingService.transfer_funds(db, "ACC-4821", "ACC-9034", 0)
    assert res_zero["status"] == "FAILED"
    assert "positive" in res_zero["error"].lower()

    res_neg = BankingService.transfer_funds(db, "ACC-4821", "ACC-9034", -500)
    assert res_neg["status"] == "FAILED"
    assert "positive" in res_neg["error"].lower()


def test_transfer_funds_same_sender_receiver(db):
    res = BankingService.transfer_funds(db, "ACC-4821", "ACC-4821", 1000.0)
    assert res["status"] == "FAILED"
    assert "cannot be the same" in res["error"].lower()


def test_transfer_funds_insufficient_funds(db):
    sender = db.query(Account).filter(Account.account_id == "ACC-4821").first()
    sender.status = "ACTIVE"
    sender.balance = 500.0
    db.commit()

    res = BankingService.transfer_funds(db, "ACC-4821", "ACC-9034", 10000.0)
    assert res["status"] == "FAILED"
    assert "insufficient funds" in res["error"].lower()


def test_transfer_funds_frozen_sender(db):
    sender = db.query(Account).filter(Account.account_id == "ACC-4821").first()
    sender.status = "FROZEN"
    sender.balance = 50000.0
    db.commit()

    res = BankingService.transfer_funds(db, "ACC-4821", "ACC-9034", 1000.0)
    assert res["status"] == "FAILED"
    assert "frozen" in res["error"].lower()


def test_transfer_funds_daily_limit_violation(db):
    sender = db.query(Account).filter(Account.account_id == "ACC-4821").first()
    sender.status = "ACTIVE"
    sender.balance = 500000.0
    sender.daily_transfer_limit = 25000.0
    db.commit()

    res = BankingService.transfer_funds(db, "ACC-4821", "ACC-9034", 50000.0)
    assert res["status"] == "FAILED"
    assert "exceeds daily limit" in res["error"].lower()


def test_transfer_funds_invalid_accounts(db):
    res_sender = BankingService.transfer_funds(db, "ACC-NONEXISTENT", "ACC-9034", 1000.0)
    assert res_sender["status"] == "FAILED"

    res_recv = BankingService.transfer_funds(db, "ACC-4821", "ACC-NONEXISTENT", 1000.0)
    assert res_recv["status"] == "FAILED"


# ── WRITE & FAILURE CONDITIONS: FREEZE / UNFREEZE ───────────────────────────

def test_freeze_and_unfreeze_lifecycle(db):
    acc = db.query(Account).filter(Account.account_id == "ACC-7742").first()
    if not acc:
        acc = Account(
            account_id="ACC-7742",
            customer_id="C-7742",
            account_type="SAVINGS",
            balance=30000.0,
            status="ACTIVE",
            daily_transfer_limit=50000.0
        )
        db.add(acc)
        db.commit()

    acc_id = "ACC-7742"

    # Freeze
    res_freeze = BankingService.freeze_account(db, acc_id, "Test Freeze")
    assert res_freeze["status"] == "SUCCESS"
    assert res_freeze["current_status"] == "FROZEN"

    # Repeated Freeze (Idempotent)
    res_freeze_again = BankingService.freeze_account(db, acc_id, "Test Freeze 2")
    assert res_freeze_again["status"] == "SUCCESS"
    assert res_freeze_again["current_status"] == "FROZEN"

    # Unfreeze
    res_unfreeze = BankingService.unfreeze_account(db, acc_id, "Test Unfreeze")
    assert res_unfreeze["status"] == "SUCCESS"
    assert res_unfreeze["current_status"] == "ACTIVE"

    # Repeated Unfreeze (Idempotent)
    res_unfreeze_again = BankingService.unfreeze_account(db, acc_id, "Test Unfreeze 2")
    assert res_unfreeze_again["status"] == "SUCCESS"
    assert res_unfreeze_again["current_status"] == "ACTIVE"


def test_freeze_invalid_account(db):
    res = BankingService.freeze_account(db, "ACC-999999")
    assert res["status"] == "FAILED"


# ── WRITE & FAILURE CONDITIONS: LOAN DISBURSEMENT ───────────────────────────

def test_loan_disbursement_lifecycle(db):
    loan = db.query(Loan).filter(Loan.approval_status == "APPROVED", Loan.disbursement_status == "PENDING").first()
    if not loan:
        cust_acc = db.query(Account).first()
        loan = Loan(
            loan_id="LOAN-TEST-001",
            customer_id=cust_acc.customer_id,
            loan_type="PERSONAL",
            amount=50000.0,
            approval_status="APPROVED",
            disbursement_status="PENDING",
            approved_by="CREDIT_OFFICER"
        )
        db.add(loan)
        db.commit()

    cust_acc = db.query(Account).filter(Account.customer_id == loan.customer_id).first()
    bal_before = cust_acc.balance

    res = BankingService.disburse_loan(db, loan.loan_id)
    assert res["status"] == "SUCCESS"
    assert res["disbursement_status"] == "DISBURSED"
    assert res["credited_account"] == cust_acc.account_id

    # Verify credit
    db.refresh(cust_acc)
    assert cust_acc.balance == bal_before + loan.amount

    # Idempotent disbursement test (already disbursed)
    res_idempotent = BankingService.disburse_loan(db, loan.loan_id)
    assert res_idempotent["status"] == "SUCCESS"
    assert "already disbursed" in res_idempotent["message"].lower()


def test_loan_disbursement_unapproved(db):
    import uuid
    loan_id = f"LOAN-UNAPP-{uuid.uuid4().hex[:6].upper()}"
    loan = Loan(
        loan_id=loan_id,
        customer_id="C-6634",
        loan_type="PERSONAL",
        amount=50000.0,
        approval_status="PENDING",
        disbursement_status="PENDING",
        approved_by=None
    )
    db.add(loan)
    db.commit()

    res = BankingService.disburse_loan(db, loan_id)
    assert res["status"] == "FAILED"
    assert "approved" in res["error"].lower()


def test_loan_disbursement_invalid_loan(db):
    res = BankingService.disburse_loan(db, "LOAN-INVALID-999")
    assert res["status"] == "FAILED"


# ── WRITE & FAILURE CONDITIONS: FRAUD STATUS UPDATES ─────────────────────────

def test_fraud_status_valid_transition(db):
    case = db.query(FraudCase).filter(FraudCase.status == "OPEN").first()
    if not case:
        import uuid
        case_id = f"FC-TEST-{uuid.uuid4().hex[:6].upper()}"
        case = FraudCase(
            case_id=case_id,
            customer_id="C-6634",
            account_id="ACC-4821",
            case_type="SUSPICIOUS_TRANSFER",
            severity="MEDIUM",
            status="OPEN",
            description="Test case"
        )
        db.add(case)
        db.commit()

    case_id = case.case_id

    # Valid transition: OPEN -> UNDER_INVESTIGATION
    res1 = FraudService.update_fraud_case(db, case_id, "UNDER_INVESTIGATION", "Assigned to analyst")
    assert res1["status"] == "SUCCESS"
    assert res1["updated_status"] == "UNDER_INVESTIGATION"

    # Valid transition: UNDER_INVESTIGATION -> RESOLVED
    res2 = FraudService.update_fraud_case(db, case_id, "RESOLVED", "Cleared by customer")
    assert res2["status"] == "SUCCESS"
    assert res2["updated_status"] == "RESOLVED"

    # Valid transition: RESOLVED -> CLOSED
    res3 = FraudService.update_fraud_case(db, case_id, "CLOSED", "Case archived")
    assert res3["status"] == "SUCCESS"
    assert res3["updated_status"] == "CLOSED"


def test_fraud_status_invalid_transition(db):
    import uuid
    case_id = f"FC-INV-{uuid.uuid4().hex[:6].upper()}"
    case = FraudCase(
        case_id=case_id,
        customer_id="C-6634",
        account_id="ACC-4821",
        case_type="PHISHING_ATTACK",
        severity="HIGH",
        status="OPEN",
        description="Test case for invalid jump"
    )
    db.add(case)
    db.commit()

    # Invalid jump: OPEN directly to RESOLVED (must be investigated first)
    res = FraudService.update_fraud_case(db, case_id, "RESOLVED")
    assert res["status"] == "FAILED"
    assert "invalid status transition" in res["error"].lower()


def test_fraud_status_invalid_status_string(db):
    res = FraudService.update_fraud_case(db, "FC-2291", "COMPLETELY_BOGUS_STATUS")
    assert res["status"] == "FAILED"
    assert "allowed statuses" in res["error"].lower()
