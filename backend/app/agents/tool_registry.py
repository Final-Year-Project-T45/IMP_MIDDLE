"""
FinSecure Tool Registry — Phase 1
==================================
All banking tools are defined here as plain callables with JSON-schema descriptors.
The LLM reads tool descriptions to decide WHEN and HOW to call each tool.
Python only executes the selected tool and returns the result.

Tool registries by agent role:
  RESEARCHER_TOOLS  — read-only: account, customer, transactions, loan, fraud case, policy
  EXECUTOR_TOOLS    — write: transfer, freeze, unfreeze, disburse, update fraud case
  AUDITOR_TOOLS     — read-only (same as researcher, for independent verification)
"""
import json
import logging
from typing import Any, Dict

logger = logging.getLogger("finsecure.tools")

# ---------------------------------------------------------------------------
# Lazy DB session factory — avoids circular imports
# ---------------------------------------------------------------------------
def _get_db():
    from app.database import SessionLocal
    return SessionLocal()

# ---------------------------------------------------------------------------
# Tool implementations (plain Python functions wrapping service layer)
# ---------------------------------------------------------------------------

def _get_account(account_id: str) -> Dict[str, Any]:
    """Retrieve a bank account record by account ID."""
    from app.services.banking_service import BankingService
    db = _get_db()
    try:
        return BankingService.get_account(db, account_id)
    finally:
        db.close()

def _get_customer(customer_id: str) -> Dict[str, Any]:
    """Retrieve a customer profile by customer ID."""
    from app.models.customer import Customer
    db = _get_db()
    try:
        cust = db.query(Customer).filter(Customer.customer_id == customer_id).first()
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
    finally:
        db.close()

def _get_transactions(account_id: str, limit: int = 5) -> Dict[str, Any]:
    """Retrieve recent transactions for an account."""
    from app.services.banking_service import BankingService
    db = _get_db()
    try:
        return BankingService.get_transactions(db, account_id, limit=limit)
    finally:
        db.close()

def _get_loan(identifier: str) -> Dict[str, Any]:
    """Retrieve a loan record by loan ID or customer ID."""
    from app.services.banking_service import BankingService
    db = _get_db()
    try:
        return BankingService.get_loan(db, identifier)
    finally:
        db.close()

def _get_fraud_case(case_id: str) -> Dict[str, Any]:
    """Retrieve a fraud case record by case ID (e.g. FC-2291)."""
    from app.services.fraud_service import FraudService
    db = _get_db()
    try:
        return FraudService.get_fraud_case(db, case_id)
    finally:
        db.close()

def _search_policy(query: str, top_k: int = 2) -> Dict[str, Any]:
    """Search the policy knowledge base with a natural language query."""
    from app.services.policy_service import policy_kb
    try:
        results = policy_kb.search(query, top_k=top_k)
        if not results:
            return {"status": "ERROR", "message": "No policy documents found for query.", "query": query}
        return {
            "status": "SUCCESS",
            "query": query,
            "results": results,
            "summary": "\n\n".join([f"[{r['title']}]\n{r['content']}" for r in results])
        }
    except Exception as e:
        return {"status": "ERROR", "message": str(e), "query": query}

def _transfer_funds(sender_account: str, receiver_account: str, amount: float, description: str = "Agent Fund Transfer") -> Dict[str, Any]:
    """Execute a fund transfer between two accounts."""
    from app.services.banking_service import BankingService
    db = _get_db()
    try:
        return BankingService.transfer_funds(db, sender_account, receiver_account, amount, description)
    finally:
        db.close()

def _freeze_account(account_id: str, reason: str = "Customer reported compromised") -> Dict[str, Any]:
    """Freeze a bank account by setting its status to FROZEN."""
    from app.services.banking_service import BankingService
    db = _get_db()
    try:
        return BankingService.freeze_account(db, account_id, reason)
    finally:
        db.close()

def _unfreeze_account(account_id: str, reason: str = "Verification complete") -> Dict[str, Any]:
    """Unfreeze a previously frozen bank account, restoring it to ACTIVE status."""
    from app.services.banking_service import BankingService
    db = _get_db()
    try:
        return BankingService.unfreeze_account(db, account_id, reason)
    finally:
        db.close()

def _disburse_loan(loan_id_or_customer: str) -> Dict[str, Any]:
    """Disburse an approved loan to the customer's primary account."""
    from app.services.banking_service import BankingService
    db = _get_db()
    try:
        return BankingService.disburse_loan(db, loan_id_or_customer)
    finally:
        db.close()

def _update_fraud_case_status(case_id: str, new_status: str, notes: str = "") -> Dict[str, Any]:
    """Update the status of a fraud case (e.g. OPEN -> UNDER_INVESTIGATION -> RESOLVED)."""
    from app.services.fraud_service import FraudService
    db = _get_db()
    try:
        return FraudService.update_fraud_case(db, case_id, new_status, notes)
    finally:
        db.close()

# ---------------------------------------------------------------------------
# OpenAI-compatible tool schema builder
# ---------------------------------------------------------------------------
def _make_tool(name: str, description: str, parameters: dict) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                **parameters
            }
        }
    }

# ---------------------------------------------------------------------------
# Tool definitions with rich descriptions (the LLM reads these!)
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = {
    "get_account": _make_tool(
        name="get_account",
        description=(
            "Retrieve the current account record for a given account identifier. "
            "Use this when you need account existence, status (ACTIVE/FROZEN), account type, "
            "current balance, customer name, or daily transfer limit. "
            "Accepts both numeric IDs (e.g. '4821') and prefixed IDs (e.g. 'ACC-4821')."
        ),
        parameters={
            "properties": {"account_id": {"type": "string", "description": "The account identifier, e.g. '4821' or 'ACC-4821'"}},
            "required": ["account_id"]
        }
    ),
    "get_customer": _make_tool(
        name="get_customer",
        description=(
            "Retrieve the customer profile for a given customer ID. "
            "Use this when you need customer personal details, KYC status, or risk profile. "
            "Accepts IDs like 'C-6634'."
        ),
        parameters={
            "properties": {"customer_id": {"type": "string", "description": "The customer identifier, e.g. 'C-6634'"}},
            "required": ["customer_id"]
        }
    ),
    "get_transactions": _make_tool(
        name="get_transactions",
        description=(
            "Retrieve recent transactions for a bank account. "
            "Use this when transaction history, recent activity, or spending patterns are needed. "
            "The 'limit' parameter controls how many transactions to return (default 5)."
        ),
        parameters={
            "properties": {
                "account_id": {"type": "string", "description": "The account identifier"},
                "limit": {"type": "integer", "description": "Number of recent transactions to retrieve (default 5)", "default": 5}
            },
            "required": ["account_id"]
        }
    ),
    "get_loan": _make_tool(
        name="get_loan",
        description=(
            "Retrieve a loan record by loan ID or customer ID. "
            "Use this when loan details, approval status, disbursement status, or loan amount are needed. "
            "Accepts loan IDs like 'LOAN-6634' or customer IDs like 'C-6634'."
        ),
        parameters={
            "properties": {"identifier": {"type": "string", "description": "Loan ID (e.g. 'LOAN-6634') or customer ID (e.g. 'C-6634')"}},
            "required": ["identifier"]
        }
    ),
    "get_fraud_case": _make_tool(
        name="get_fraud_case",
        description=(
            "Retrieve a fraud case record by its case ID. "
            "Use this when investigating fraud reports, checking fraud case status, severity, "
            "or identifying the account associated with a fraud investigation. "
            "Accepts IDs like 'FC-2291'."
        ),
        parameters={
            "properties": {"case_id": {"type": "string", "description": "Fraud case ID, e.g. 'FC-2291'"}},
            "required": ["case_id"]
        }
    ),
    "search_policy": _make_tool(
        name="search_policy",
        description=(
            "Search the FinSecure internal policy knowledge base using a natural language query. "
            "Use this when policy rules, transfer limits, compliance requirements, or operational guidelines are needed. "
            "Examples: 'retail wire transfer daily limit', 'account freeze policy', 'loan disbursement requirements'."
        ),
        parameters={
            "properties": {
                "query": {"type": "string", "description": "Natural language policy search query"},
                "top_k": {"type": "integer", "description": "Number of policy documents to retrieve (default 2)", "default": 2}
            },
            "required": ["query"]
        }
    ),
    "transfer_funds": _make_tool(
        name="transfer_funds",
        description=(
            "Execute a wire fund transfer from one account to another in the FinSecure banking system. "
            "Use ONLY when the task explicitly requires moving funds between accounts. "
            "The system enforces balance checks, daily limits, and account status validation automatically. "
            "Requires sender account ID, receiver account ID, and amount in rupees."
        ),
        parameters={
            "properties": {
                "sender_account": {"type": "string", "description": "Sender account ID"},
                "receiver_account": {"type": "string", "description": "Receiver account ID"},
                "amount": {"type": "number", "description": "Transfer amount in rupees"},
                "description": {"type": "string", "description": "Transfer description/memo", "default": "Agent Fund Transfer"}
            },
            "required": ["sender_account", "receiver_account", "amount"]
        }
    ),
    "freeze_account": _make_tool(
        name="freeze_account",
        description=(
            "Set a bank account status to FROZEN, preventing all transactions. "
            "Use when the customer reports the account as compromised, or fraud is detected. "
            "Requires account ID and a reason for freezing."
        ),
        parameters={
            "properties": {
                "account_id": {"type": "string", "description": "Account ID to freeze"},
                "reason": {"type": "string", "description": "Reason for freezing the account", "default": "Customer reported compromised"}
            },
            "required": ["account_id"]
        }
    ),
    "unfreeze_account": _make_tool(
        name="unfreeze_account",
        description=(
            "Restore a FROZEN bank account back to ACTIVE status. "
            "Use only when verification is complete and the account can safely resume operations."
        ),
        parameters={
            "properties": {
                "account_id": {"type": "string", "description": "Account ID to unfreeze"},
                "reason": {"type": "string", "description": "Reason for unfreezing", "default": "Verification complete"}
            },
            "required": ["account_id"]
        }
    ),
    "disburse_loan": _make_tool(
        name="disburse_loan",
        description=(
            "Disburse an approved loan by crediting the loan amount to the customer's primary bank account. "
            "Only APPROVED loans can be disbursed. Already-disbursed loans are idempotently handled. "
            "Accepts a loan ID (e.g. 'LOAN-6634') or customer ID (e.g. 'C-6634')."
        ),
        parameters={
            "properties": {"loan_id_or_customer": {"type": "string", "description": "Loan ID or Customer ID"}},
            "required": ["loan_id_or_customer"]
        }
    ),
    "update_fraud_case_status": _make_tool(
        name="update_fraud_case_status",
        description=(
            "Update the investigation status of a fraud case. "
            "Valid statuses: OPEN, UNDER_INVESTIGATION, RESOLVED, CLOSED. "
            "Use when a fraud investigation progresses or is resolved."
        ),
        parameters={
            "properties": {
                "case_id": {"type": "string", "description": "Fraud case ID, e.g. 'FC-2291'"},
                "new_status": {"type": "string", "description": "New status: OPEN, UNDER_INVESTIGATION, RESOLVED, or CLOSED"},
                "notes": {"type": "string", "description": "Investigation notes", "default": ""}
            },
            "required": ["case_id", "new_status"]
        }
    ),
}

# ---------------------------------------------------------------------------
# Agent-scoped tool registries
# ---------------------------------------------------------------------------

RESEARCHER_TOOL_NAMES = ["get_account", "get_customer", "get_transactions", "get_loan", "get_fraud_case", "search_policy"]
EXECUTOR_TOOL_NAMES   = ["transfer_funds", "freeze_account", "unfreeze_account", "disburse_loan", "update_fraud_case_status"]
AUDITOR_TOOL_NAMES    = ["get_account", "get_transactions", "get_fraud_case", "get_loan", "search_policy"]

RESEARCHER_TOOLS = [TOOL_SCHEMAS[n] for n in RESEARCHER_TOOL_NAMES]
EXECUTOR_TOOLS   = [TOOL_SCHEMAS[n] for n in EXECUTOR_TOOL_NAMES]
AUDITOR_TOOLS    = [TOOL_SCHEMAS[n] for n in AUDITOR_TOOL_NAMES]

# ---------------------------------------------------------------------------
# Tool dispatcher — executes a named tool with JSON arguments
# ---------------------------------------------------------------------------

TOOL_IMPLEMENTATIONS = {
    "get_account":            lambda args: _get_account(**args),
    "get_customer":           lambda args: _get_customer(**args),
    "get_transactions":       lambda args: _get_transactions(**args),
    "get_loan":               lambda args: _get_loan(**args),
    "get_fraud_case":         lambda args: _get_fraud_case(**args),
    "search_policy":          lambda args: _search_policy(**args),
    "transfer_funds":         lambda args: _transfer_funds(**args),
    "freeze_account":         lambda args: _freeze_account(**args),
    "unfreeze_account":       lambda args: _unfreeze_account(**args),
    "disburse_loan":          lambda args: _disburse_loan(**args),
    "update_fraud_case_status": lambda args: _update_fraud_case_status(**args),
}

def execute_tool(tool_name: str, tool_args: dict) -> dict:
    """
    Validate and execute a named tool.
    The LLM selects the tool; Python executes it safely within the allowlist.
    No arbitrary code, SQL, or shell execution is possible here.
    """
    if tool_name not in TOOL_IMPLEMENTATIONS:
        logger.error(f"Unknown tool requested: {tool_name}")
        return {"status": "ERROR", "message": f"Tool '{tool_name}' is not registered in the FinSecure tool allowlist."}
    try:
        logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
        result = TOOL_IMPLEMENTATIONS[tool_name](tool_args)
        logger.info(f"Tool {tool_name} result status: {result.get('status', 'unknown')}")
        return result
    except Exception as e:
        logger.error(f"Tool execution error for {tool_name}: {e}")
        return {"status": "ERROR", "message": f"Tool '{tool_name}' execution failed: {str(e)}"}
