from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.config import settings
from app.database import engine, Base
from app.seed_data import seed_database
from app.api.tasks import router as tasks_router
from app.api.banking import router as banking_router
from app.api.fraud import router as fraud_router
from app.api.policies import router as policies_router
from app.api.audit import router as audit_router

# Initialize database tables & seed data on startup
Base.metadata.create_all(bind=engine)
seed_database()

app = FastAPI(
    title="FinSecure — Autonomous Banking Operations Platform (Phase 1 Baseline)",
    description="Simulated Autonomous Banking Workflow powered by a 5-Agent LangGraph Architecture.",
    version="1.0.0"
)

# CORS configuration for frontend interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(tasks_router)
app.include_router(banking_router)
app.include_router(fraud_router)
app.include_router(policies_router)
app.include_router(audit_router)

@app.get("/")
def root():
    return {
        "system": "FinSecure — Autonomous Bank Operations & Fraud-Investigation Platform",
        "phase": "Phase 1 Baseline (Unprotected)",
        "agents": ["Orchestrator", "Planner", "Researcher", "Executor", "Auditor"],
        "status": "ONLINE"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
