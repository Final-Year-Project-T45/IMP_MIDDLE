import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.models.loan import Loan
from app.models.audit_event import AuditEvent

class BankingService:
    @staticmethod
    def get_account(db: Session, account_id: str) -> Dict[str, Any]:
        acc = db.query(Account).filter(Account.account_id == account_id).first()
        if not acc:
            # Try fuzzy match for suffix, e.g. 4821 -> ACC-4821
            acc = db.query(Account).filter(Account.account_id.endswith(account_id)).first()
            
        if not acc:
            return {"status": "ERROR", "account_id": account_id, "message": f"Account '{account_id}' not found."}
            
        cust = db.query(Customer).filter(Customer.customer_id == acc.customer_id).first()
        return {
            "status": "SUCCESS",
            "account_id": acc.account_id,
            "customer_id": acc.customer_id,
            "customer_name": cust.name if cust else "Unknown",
            "account_type": acc.account_type,
            "balance": acc.balance,
            "account_status": acc.status,
            "daily_transfer_limit": acc.daily_transfer_limit,
            "created_at": acc.created_at.isoformat() if acc.created_at else None
        }

    @staticmethod
    def get_customer(db: Session, customer_id: str) -> Dict[str, Any]:
        cust = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not cust:
            cust = db.query(Customer).filter(Customer.customer_id.endswith(customer_id)).first()
        if not cust:
            return {"status": "ERROR", "customer_id": customer_id, "message": f"Customer '{customer_id}' not found."}
        return {
            "status": "SUCCESS",
            "customer_id": cust.customer_id,
            "name": cust.name,
            "email": cust.email,
            "phone": cust.phone,
            "kyc_status": cust.kyc_status,
            "risk_level": cust.risk_level,
            "created_at": cust.created_at.isoformat() if cust.created_at else None,
        }

    @staticmethod
    def get_balance(db: Session, account_id: str) -> Dict[str, Any]:
        res = BankingService.get_account(db, account_id)
        if res.get("status") == "ERROR":
            return res
        return {
            "status": "SUCCESS",
            "account_id": res["account_id"],
            "balance": res["balance"],
            "account_status": res["status"]
        }

    @staticmethod
    def get_transactions(db: Session, account_id: str, limit: int = 5) -> Dict[str, Any]:
        acc_res = BankingService.get_account(db, account_id)
        if acc_res.get("status") == "ERROR":
            return acc_res
            
        target_id = acc_res["account_id"]
        txs = db.query(Transaction).filter(
            (Transaction.sender_account == target_id) | (Transaction.receiver_account == target_id)
        ).order_by(Transaction.timestamp.desc()).limit(limit).all()

        tx_list = []
        for t in txs:
            tx_list.append({
                "transaction_id": t.transaction_id,
                "sender_account": t.sender_account,
                "receiver_account": t.receiver_account,
                "amount": t.amount,
                "transaction_type": t.transaction_type,
                "status": t.status,
                "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                "description": t.description
            })

        return {
            "status": "SUCCESS",
            "account_id": target_id,
            "count": len(tx_list),
            "transactions": tx_list
        }

    @staticmethod
    def transfer_funds(db: Session, sender_account: str, receiver_account: str, amount: float, description: str = "Executor Agent Transfer") -> Dict[str, Any]:
        # 1. Validate Amount
        if amount is None or amount <= 0:
            return {"status": "FAILED", "error": f"Invalid transfer amount: ₹{amount}. Transfer amount must be positive."}

        # 2. Resolve Sender
        sender_res = BankingService.get_account(db, sender_account)
        if sender_res.get("status") == "ERROR":
            return {"status": "FAILED", "error": f"Sender account error: {sender_res.get('message')}"}

        # 3. Resolve Receiver
        receiver_res = BankingService.get_account(db, receiver_account)
        if receiver_res.get("status") == "ERROR":
            return {"status": "FAILED", "error": f"Receiver account error: {receiver_res.get('message')}"}

        sender = db.query(Account).filter(Account.account_id == sender_res["account_id"]).first()
        receiver = db.query(Account).filter(Account.account_id == receiver_res["account_id"]).first()

        # 4. Check Same Sender / Receiver
        if sender.account_id == receiver.account_id:
            return {"status": "FAILED", "error": f"Sender and receiver accounts cannot be the same ({sender.account_id})."}

        # 5. Check Account Statuses
        if sender.status != "ACTIVE":
            return {"status": "FAILED", "error": f"Sender account '{sender.account_id}' is {sender.status}. Transfer rejected."}
        if receiver.status != "ACTIVE":
            return {"status": "FAILED", "error": f"Receiver account '{receiver.account_id}' is {receiver.status}. Transfer rejected."}

        # 6. Check Sufficient Balance
        if sender.balance < amount:
            return {"status": "FAILED", "error": f"Insufficient funds. Sender balance is ₹{sender.balance:,.2f}, requested ₹{amount:,.2f}."}

        # 7. Check Transfer Limit
        if amount > sender.daily_transfer_limit:
            return {"status": "FAILED", "error": f"Transfer amount ₹{amount:,.2f} exceeds daily limit ₹{sender.daily_transfer_limit:,.2f}."}

        # 8. Record Snapshot Balances for Invariant Verification
        sender_before = sender.balance
        receiver_before = receiver.balance

        # 9. Execute Transaction inside DB Transaction block
        tx_id = f"TX-{uuid.uuid4().hex[:8].upper()}"
        try:
            sender.balance -= amount
            receiver.balance += amount
            sender_after = sender.balance
            receiver_after = receiver.balance

            tx = Transaction(
                transaction_id=tx_id,
                sender_account=sender.account_id,
                receiver_account=receiver.account_id,
                amount=amount,
                transaction_type="WIRE_TRANSFER",
                status="SUCCESS",
                initiated_by="EXECUTOR_AGENT",
                description=description
            )
            db.add(tx)
            db.commit()

            return {
                "status": "SUCCESS",
                "transaction_id": tx_id,
                "sender_account": sender.account_id,
                "receiver_account": receiver.account_id,
                "amount": amount,
                "sender_before_balance": sender_before,
                "receiver_before_balance": receiver_before,
                "sender_new_balance": sender_after,
                "receiver_new_balance": receiver_after,
                "message": f"Successfully transferred ₹{amount:,.2f} from {sender.account_id} to {receiver.account_id}."
            }
        except Exception as e:
            db.rollback()
            return {"status": "FAILED", "error": f"Database transaction failed: {str(e)}"}

    @staticmethod
    def freeze_account(db: Session, account_id: str, reason: str = "Customer reported compromised") -> Dict[str, Any]:
        acc_res = BankingService.get_account(db, account_id)
        if acc_res.get("status") == "ERROR":
            return {"status": "FAILED", "error": acc_res.get("message")}

        acc = db.query(Account).filter(Account.account_id == acc_res["account_id"]).first()
        prev_status = acc.status
        if prev_status == "FROZEN":
            return {
                "status": "SUCCESS",
                "account_id": acc.account_id,
                "previous_status": "FROZEN",
                "current_status": "FROZEN",
                "message": f"Account '{acc.account_id}' was already FROZEN."
            }

        try:
            acc.status = "FROZEN"
            db.commit()
            return {
                "status": "SUCCESS",
                "account_id": acc.account_id,
                "previous_status": prev_status,
                "current_status": "FROZEN",
                "reason": reason,
                "message": f"Account '{acc.account_id}' status successfully updated from {prev_status} to FROZEN."
            }
        except Exception as e:
            db.rollback()
            return {"status": "FAILED", "error": f"Failed to freeze account: {str(e)}"}

    @staticmethod
    def unfreeze_account(db: Session, account_id: str, reason: str = "Verification complete") -> Dict[str, Any]:
        acc_res = BankingService.get_account(db, account_id)
        if acc_res.get("status") == "ERROR":
            return {"status": "FAILED", "error": acc_res.get("message")}

        acc = db.query(Account).filter(Account.account_id == acc_res["account_id"]).first()
        prev_status = acc.status
        if prev_status == "ACTIVE":
            return {
                "status": "SUCCESS",
                "account_id": acc.account_id,
                "previous_status": "ACTIVE",
                "current_status": "ACTIVE",
                "message": f"Account '{acc.account_id}' was already ACTIVE."
            }

        try:
            acc.status = "ACTIVE"
            db.commit()
            return {
                "status": "SUCCESS",
                "account_id": acc.account_id,
                "previous_status": prev_status,
                "current_status": "ACTIVE",
                "reason": reason,
                "message": f"Account '{acc.account_id}' un-frozen successfully."
            }
        except Exception as e:
            db.rollback()
            return {"status": "FAILED", "error": str(e)}

    @staticmethod
    def get_loan(db: Session, identifier: str) -> Dict[str, Any]:
        loan = db.query(Loan).filter((Loan.loan_id == identifier) | (Loan.customer_id == identifier)).first()
        if not loan:
            return {"status": "ERROR", "loan_id": identifier, "message": f"Loan record for '{identifier}' not found."}

        cust = db.query(Customer).filter(Customer.customer_id == loan.customer_id).first()
        return {
            "status": "SUCCESS",
            "loan_id": loan.loan_id,
            "customer_id": loan.customer_id,
            "customer_name": cust.name if cust else "Unknown",
            "loan_type": loan.loan_type,
            "amount": loan.amount,
            "approval_status": loan.approval_status,
            "disbursement_status": loan.disbursement_status,
            "approved_by": loan.approved_by,
            "created_at": loan.created_at.isoformat() if loan.created_at else None,
            "disbursed_at": loan.disbursed_at.isoformat() if loan.disbursed_at else None
        }

    @staticmethod
    def disburse_loan(db: Session, loan_id_or_customer: str) -> Dict[str, Any]:
        loan_res = BankingService.get_loan(db, loan_id_or_customer)
        if loan_res.get("status") == "ERROR":
            return {"status": "FAILED", "error": loan_res.get("message")}

        loan = db.query(Loan).filter(Loan.loan_id == loan_res["loan_id"]).first()
        
        # Check Approval
        if loan.approval_status != "APPROVED":
            return {"status": "FAILED", "error": f"Loan '{loan.loan_id}' is in status '{loan.approval_status}'. Only APPROVED loans can be disbursed."}

        # Check Idempotency (Already disbursed?)
        if loan.disbursement_status == "DISBURSED":
            return {
                "status": "SUCCESS",
                "loan_id": loan.loan_id,
                "disbursement_status": "DISBURSED",
                "amount": loan.amount,
                "message": f"Loan '{loan.loan_id}' was already disbursed on {loan.disbursed_at}. No duplicate funds released."
            }

        # Find customer primary account to credit
        cust_acc = db.query(Account).filter(Account.customer_id == loan.customer_id).first()
        if not cust_acc:
            return {"status": "FAILED", "error": f"Customer '{loan.customer_id}' has no associated active account to receive loan credit."}

        tx_id = f"TX-DISB-{uuid.uuid4().hex[:6].upper()}"
        now = datetime.now(timezone.utc)
        try:
            cust_acc.balance += loan.amount
            loan.disbursement_status = "DISBURSED"
            loan.disbursed_at = now

            tx = Transaction(
                transaction_id=tx_id,
                sender_account="BANK_LOAN_POOL",
                receiver_account=cust_acc.account_id,
                amount=loan.amount,
                transaction_type="LOAN_DISBURSEMENT",
                status="SUCCESS",
                initiated_by="EXECUTOR_AGENT",
                description=f"Disbursement for approved loan {loan.loan_id}"
            )
            db.add(tx)
            db.commit()

            return {
                "status": "SUCCESS",
                "loan_id": loan.loan_id,
                "customer_id": loan.customer_id,
                "disbursement_status": "DISBURSED",
                "amount": loan.amount,
                "credited_account": cust_acc.account_id,
                "new_account_balance": cust_acc.balance,
                "transaction_id": tx_id,
                "disbursed_at": now.isoformat(),
                "message": f"Successfully disbursed loan ₹{loan.amount:,.2f} for customer {loan.customer_id} into account {cust_acc.account_id}."
            }
        except Exception as e:
            db.rollback()
            return {"status": "FAILED", "error": f"Disbursement failed: {str(e)}"}
