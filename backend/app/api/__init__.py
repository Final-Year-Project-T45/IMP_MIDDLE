from app.api.tasks import router as tasks_router
from app.api.banking import router as banking_router
from app.api.fraud import router as fraud_router
from app.api.policies import router as policies_router
from app.api.audit import router as audit_router

__all__ = [
    "tasks_router",
    "banking_router",
    "fraud_router",
    "policies_router",
    "audit_router"
]
