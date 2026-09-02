from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class SignedHeader(BaseModel):
    sender_id: str
    receiver_id: str
    task_id: str
    timestamp: str
    nonce: str
    capability: Optional[str] = None
    payload_hash: str
    parent_event_id: Optional[str] = None
    delegation_id: Optional[str] = None
    signature: str

class DelegationToken(BaseModel):
    token_id: str
    issuer_id: str
    subject_id: str
    task_id: str
    capability: str
    scope: Dict[str, Any] = Field(default_factory=dict)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    issued_at: str
    expires_at: str
    nonce: str
    signature: str

class PromptResult(BaseModel):
    risk_score: float = 0.0
    label: str = "SAFE"  # SAFE, SUSPICIOUS, MALICIOUS
    indicators: List[str] = Field(default_factory=list)

class SecurityEventSchema(BaseModel):
    event_id: str
    timestamp: str
    task_id: str
    agent_id: str
    sender_id: Optional[str] = None
    receiver_id: Optional[str] = None
    action: str
    capability: Optional[str] = None
    action_tier: str = "TIER_1"
    trust_before: float = 1.0
    anomaly_severity: float = 0.0
    trust_after: float = 1.0
    prompt_risk: float = 0.0
    policy_decision: str = "ALLOW"
    provenance_decision: str = "VALID"
    adaptive_decision: str = "ALLOW"
    result: str = "SUCCESS"
    parent_event_id: Optional[str] = None
    event_hash: Optional[str] = None
    merkle_root: Optional[str] = None

class ProvenanceNodeSchema(BaseModel):
    event_id: str
    task_id: str
    agent_id: str
    parent_event_id: Optional[str] = None
    sender_id: Optional[str] = None
    receiver_id: Optional[str] = None
    action: str
    capability: Optional[str] = None
    payload_hash: str
    trust_snapshot: float = 1.0
    policy_decision: str = "ALLOW"
    timestamp: str
    node_hash: str
    signature: str
