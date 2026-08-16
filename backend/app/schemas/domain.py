from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class TaskCreateRequest(BaseModel):
    request: str
    user_id: Optional[str] = "EMP-1092"

class TransferRequest(BaseModel):
    sender_account: str
    receiver_account: str
    amount: float
    description: Optional[str] = "Direct operational transfer"

class FreezeAccountRequest(BaseModel):
    reason: Optional[str] = "Customer reported compromised"

class DisburseLoanRequest(BaseModel):
    loan_id: str

class AccountResponse(BaseModel):
    account_id: str
    customer_id: str
    account_type: str
    balance: float
    status: str
    daily_transfer_limit: float
    
    class Config:
        from_attributes = True

class CustomerResponse(BaseModel):
    customer_id: str
    name: str
    email: str
    phone: str
    customer_type: str
    kyc_status: str
    risk_level: str

    class Config:
        from_attributes = True

class TransactionResponse(BaseModel):
    transaction_id: str
    sender_account: str
    receiver_account: str
    amount: float
    transaction_type: str
    status: str
    timestamp: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class LoanResponse(BaseModel):
    loan_id: str
    customer_id: str
    loan_type: str
    amount: float
    approval_status: str
    disbursement_status: str
    approved_by: str
    
    class Config:
        from_attributes = True

class FraudCaseResponse(BaseModel):
    case_id: str
    customer_id: str
    account_id: str
    case_type: str
    severity: str
    status: str
    description: str
    assigned_analyst: str
    
    class Config:
        from_attributes = True

class AuditEventResponse(BaseModel):
    event_id: int
    task_id: str
    timestamp: str
    source_agent: str
    destination_agent: str
    event_type: str
    action_summary: str
    status: str

    class Config:
        from_attributes = True
