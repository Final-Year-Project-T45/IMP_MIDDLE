import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, JSON, Integer
from app.database import Base

class AgentIdentity(Base):
    """Stores agent identities, roles, public keys, and current trust levels."""
    __tablename__ = "agent_identities"

    agent_id = Column(String, primary_key=True)  # e.g. "AGENT-ORCHESTRATOR-01" or "Orchestrator"
    role = Column(String, nullable=False)        # Orchestrator, Planner, Researcher, Executor, Auditor
    public_key_pem = Column(Text, nullable=False) # Cryptographic public key (Ed25519/ECDSA)
    status = Column(String, default="ACTIVE")    # ACTIVE, SUSPENDED, ISOLATED, REVOKED
    capabilities = Column(JSON, default=list)    # Allowlisted action capability strings
    trust_score = Column(Float, default=1.0)     # Time-varying trust score in [0.0, 1.0]
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class DelegationTokenRecord(Base):
    """Persistent storage for short-lived, scoped delegation tokens."""
    __tablename__ = "delegation_tokens"

    token_id = Column(String, primary_key=True, default=lambda: f"DEL-{uuid.uuid4().hex[:8].upper()}")
    issuer_id = Column(String, nullable=False)   # Issuing agent ID
    subject_id = Column(String, nullable=False)  # Delegate agent ID
    task_id = Column(String, nullable=False)     # Bound task ID
    capability = Column(String, nullable=False)  # Target action capability
    scope = Column(JSON, default=dict)           # Parameters/scope constraints
    constraints = Column(JSON, default=dict)     # Max transfer amount, target account, etc.
    issued_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)
    signature = Column(Text, nullable=False)     # Cryptographic signature by issuer

class SecurityEventRecord(Base):
    """Immutable audit ledger for security decisions and trust events."""
    __tablename__ = "security_events"

    event_id = Column(String, primary_key=True, default=lambda: f"SECEVT-{uuid.uuid4().hex[:10].upper()}")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    task_id = Column(String, nullable=False)
    agent_id = Column(String, nullable=False)
    sender_id = Column(String, nullable=True)
    receiver_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    capability = Column(String, nullable=True)
    action_tier = Column(String, default="TIER_1") # TIER_1 (low risk), TIER_2 (sensitive mutation)
    trust_before = Column(Float, default=1.0)
    anomaly_severity = Column(Float, default=0.0)
    trust_after = Column(Float, default=1.0)
    prompt_risk = Column(Float, default=0.0)
    policy_decision = Column(String, default="ALLOW")
    provenance_decision = Column(String, default="VALID")
    adaptive_decision = Column(String, default="ALLOW") # ALLOW, RESTRICT, BLOCK, ISOLATE, ESCALATE
    result = Column(String, default="SUCCESS")
    parent_event_id = Column(String, nullable=True)
    event_hash = Column(String, nullable=True)
    merkle_root = Column(String, nullable=True)

class ProvenanceNodeRecord(Base):
    """DAG lineage node recording full execution derivation history."""
    __tablename__ = "provenance_nodes"

    event_id = Column(String, primary_key=True)
    task_id = Column(String, nullable=False)
    agent_id = Column(String, nullable=False)
    parent_event_id = Column(String, nullable=True)
    sender_id = Column(String, nullable=True)
    receiver_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    capability = Column(String, nullable=True)
    payload_hash = Column(String, nullable=False)
    trust_snapshot = Column(Float, default=1.0)
    policy_decision = Column(String, default="ALLOW")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    node_hash = Column(String, nullable=False)
    signature = Column(Text, nullable=False)
