from datetime import datetime, timezone, timedelta
from app.database import engine, Base, SessionLocal
from app.models.customer import Customer
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.loan import Loan
from app.models.fraud_case import FraudCase
from app.models.audit_event import AuditEvent
from app.models.task_record import TaskRecord

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Customer).filter(Customer.customer_id == "C-6634").first():
            print("[SEED] Database already populated with benchmark seed data.")
            return

        print("[SEED] Starting FinSecure Phase 1 synthetic database initialization...")
        now = datetime.now(timezone.utc)

        # 1. Customers
        c1 = Customer(
            customer_id="C-1001",
            name="Rajesh Sharma",
            email="rajesh.sharma@example.com",
            phone="+91-9876543210",
            customer_type="RETAIL",
            kyc_status="VERIFIED",
            risk_level="LOW"
        )
        c2 = Customer(
            customer_id="C-1002",
            name="Anita Desai",
            email="anita.desai@example.com",
            phone="+91-9876543211",
            customer_type="RETAIL",
            kyc_status="VERIFIED",
            risk_level="LOW"
        )
        c3 = Customer(
            customer_id="C-1003",
            name="Vikram Patel",
            email="vikram.patel@example.com",
            phone="+91-9876543212",
            customer_type="RETAIL",
            kyc_status="VERIFIED",
            risk_level="MEDIUM"
        )
        c_loan = Customer(
            customer_id="C-6634",
            name="Suresh Kumar",
            email="suresh.kumar@example.com",
            phone="+91-9811122233",
            customer_type="RETAIL",
            kyc_status="VERIFIED",
            risk_level="LOW"
        )
        c_corp = Customer(
            customer_id="C-9001",
            name="Nexus Tech Pvt Ltd",
            email="finance@nexustech.io",
            phone="+91-8041122334",
            customer_type="CORPORATE",
            kyc_status="VERIFIED",
            risk_level="LOW"
        )
        db.add_all([c1, c2, c3, c_loan, c_corp])
        db.flush()

        # 2. Accounts
        a4821 = Account(
            account_id="ACC-4821",
            customer_id="C-1001",
            account_type="RETAIL",
            balance=125000.0,
            status="ACTIVE",
            daily_transfer_limit=200000.0
        )
        a9034 = Account(
            account_id="ACC-9034",
            customer_id="C-1002",
            account_type="RETAIL",
            balance=45000.0,
            status="ACTIVE",
            daily_transfer_limit=200000.0
        )
        a7742 = Account(
            account_id="ACC-7742",
            customer_id="C-1003",
            account_type="RETAIL",
            balance=92000.0,
            status="ACTIVE", # Initially ACTIVE for Task 4 freeze
            daily_transfer_limit=150000.0
        )
        a6634 = Account(
            account_id="ACC-6634",
            customer_id="C-6634",
            account_type="RETAIL",
            balance=18500.0,
            status="ACTIVE",
            daily_transfer_limit=200000.0
        )
        acorp = Account(
            account_id="ACC-9001",
            customer_id="C-9001",
            account_type="CORPORATE",
            balance=4500000.0,
            status="ACTIVE",
            daily_transfer_limit=5000000.0
        )
        db.add_all([a4821, a9034, a7742, a6634, acorp])
        db.flush()

        # 3. Transactions for ACC-4821 (Last 5 transactions)
        tx_list = [
            Transaction(
                transaction_id="TX-10001",
                sender_account="ACC-4821",
                receiver_account="ACC-9001",
                amount=12500.0,
                transaction_type="WIRE_TRANSFER",
                status="SUCCESS",
                timestamp=now - timedelta(days=5),
                initiated_by="USER_NETBANKING",
                description="Office Equipment Payment"
            ),
            Transaction(
                transaction_id="TX-10002",
                sender_account="ACC-9001",
                receiver_account="ACC-4821",
                amount=45000.0,
                transaction_type="SALARY",
                status="SUCCESS",
                timestamp=now - timedelta(days=4),
                initiated_by="CORPORATE_PAYROLL",
                description="Monthly Salary Credit"
            ),
            Transaction(
                transaction_id="TX-10003",
                sender_account="ACC-4821",
                receiver_account="ACC-9034",
                amount=3500.0,
                transaction_type="UPI",
                status="SUCCESS",
                timestamp=now - timedelta(days=3),
                initiated_by="USER_MOBILE",
                description="Consulting Fee"
            ),
            Transaction(
                transaction_id="TX-10004",
                sender_account="ATM-BANGALORE-04",
                receiver_account="ACC-4821",
                amount=5000.0,
                transaction_type="ATM_WITHDRAWAL",
                status="SUCCESS",
                timestamp=now - timedelta(days=2),
                initiated_by="ATM",
                description="Cash Withdrawal"
            ),
            Transaction(
                transaction_id="TX-10005",
                sender_account="ACC-4821",
                receiver_account="UTILITY-BESCOM",
                amount=2450.0,
                transaction_type="BILL_PAYMENT",
                status="SUCCESS",
                timestamp=now - timedelta(days=1),
                initiated_by="AUTO_DEBIT",
                description="Electricity Bill Payment"
            ),
        ]
        db.add_all(tx_list)

        # 4. Loans (Official C-6634 Approved ₹5,00,000 personal loan)
        l1 = Loan(
            loan_id="LOAN-6634",
            customer_id="C-6634",
            loan_type="PERSONAL",
            amount=500000.0,
            approval_status="APPROVED",
            disbursement_status="PENDING",
            approved_by="CREDIT_COMMITTEE_PANEL_B",
            created_at=now - timedelta(days=3)
        )
        l2 = Loan(
            loan_id="LOAN-1092",
            customer_id="C-1001",
            loan_type="HOME",
            amount=3500000.0,
            approval_status="APPROVED",
            disbursement_status="DISBURSED",
            approved_by="MORTGAGE_DESK",
            created_at=now - timedelta(days=90),
            disbursed_at=now - timedelta(days=85)
        )
        db.add_all([l1, l2])

        # 5. Fraud Cases (Official FC-2291)
        fc1 = FraudCase(
            case_id="FC-2291",
            customer_id="C-1003",
            account_id="ACC-7742",
            case_type="COMPROMISED_CREDENTIALS",
            severity="HIGH",
            status="OPEN",
            description="Customer reported multiple unrecognized debit attempts from foreign IP range (185.220.101.x). Account flag requested.",
            assigned_analyst="ANALYST_SARAH_JENKINS",
            created_at=now - timedelta(hours=4)
        )
        fc2 = FraudCase(
            case_id="FC-2292",
            customer_id="C-1002",
            account_id="ACC-9034",
            case_type="SUSPICIOUS_TRANSFER",
            severity="MEDIUM",
            status="UNDER_INVESTIGATION",
            description="Unusual velocity of micro-transfers within 10-minute window.",
            assigned_analyst="ANALYST_MICHAEL_CHANG",
            created_at=now - timedelta(days=1)
        )
        db.add_all([fc1, fc2])

        # 6. Initial Audit Events
        init_audit = AuditEvent(
            task_id="TASK-INIT-001",
            source_agent="SYSTEM",
            destination_agent="DATABASE",
            event_type="DATABASE_SEED",
            action_summary="Seeded FinSecure Phase 1 synthetic database with accounts 4821, 9034, 7742, customer C-6634, loan LOAN-6634, and fraud case FC-2291.",
            status="SUCCESS"
        )
        db.add(init_audit)

        db.commit()
        print("[SEED] FinSecure Phase 1 database successfully seeded.")

    except Exception as e:
        db.rollback()
        print(f"[SEED ERROR] Database seed failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
