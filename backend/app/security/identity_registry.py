import hashlib
import hmac
import base64
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("finsecure.security.identity")

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

DEFAULT_AGENT_ROLES = {
    "Orchestrator": {
        "agent_id": "AGENT-ORCHESTRATOR",
        "role": "Orchestrator",
        "capabilities": ["task_route", "response_synthesize"],
        "secret_seed": "finsecure_orchestrator_secret_key_v1"
    },
    "Planner": {
        "agent_id": "AGENT-PLANNER",
        "role": "Planner",
        "capabilities": ["task_decompose", "plan_generate"],
        "secret_seed": "finsecure_planner_secret_key_v1"
    },
    "Researcher": {
        "agent_id": "AGENT-RESEARCHER",
        "role": "Researcher",
        "capabilities": ["get_account", "get_customer", "get_transactions", "get_loan", "get_fraud_case", "search_policy"],
        "secret_seed": "finsecure_researcher_secret_key_v1"
    },
    "Executor": {
        "agent_id": "AGENT-EXECUTOR",
        "role": "Executor",
        "capabilities": ["transfer_funds", "freeze_account", "unfreeze_account", "disburse_loan", "update_fraud_case_status"],
        "secret_seed": "finsecure_executor_secret_key_v1"
    },
    "Auditor": {
        "agent_id": "AGENT-AUDITOR",
        "role": "Auditor",
        "capabilities": ["audit_review", "verify_invariants", "provenance_check"],
        "secret_seed": "finsecure_auditor_secret_key_v1"
    }
}

class AgentIdentityRegistry:
    """
    Manages agent cryptographic key pairs, role capabilities, message signing,
    signature verification, and replay protection.
    """

    def __init__(self):
        self._private_keys: Dict[str, Any] = {}
        self._public_keys_pem: Dict[str, str] = {}
        self._capabilities: Dict[str, list] = {}
        self._status: Dict[str, str] = {}
        self._used_nonces: set = set()
        self._initialize_keys()

    def _initialize_keys(self):
        for role_name, config in DEFAULT_AGENT_ROLES.items():
            agent_id = config["agent_id"]
            self._capabilities[agent_id] = config["capabilities"]
            self._status[agent_id] = "ACTIVE"

            if HAS_CRYPTOGRAPHY:
                # Derive deterministic Ed25519 private key from seed bytes
                seed_bytes = hashlib.sha256(config["secret_seed"].encode("utf-8")).digest()
                priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(seed_bytes)
                pub_key = priv_key.public_key()
                pub_pem = pub_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode("utf-8")
                self._private_keys[agent_id] = priv_key
                self._public_keys_pem[agent_id] = pub_pem
            else:
                # HMAC fallback secret
                self._private_keys[agent_id] = config["secret_seed"].encode("utf-8")
                self._public_keys_pem[agent_id] = f"HMAC-SHA256:{hashlib.sha256(config['secret_seed'].encode('utf-8')).hexdigest()}"

    def get_agent_id(self, role: str) -> str:
        role_clean = role.strip().capitalize()
        for r, cfg in DEFAULT_AGENT_ROLES.items():
            if r.lower() == role_clean.lower():
                return cfg["agent_id"]
        return f"AGENT-{role.upper()}"

    def get_capabilities(self, agent_id: str) -> list:
        return self._capabilities.get(agent_id, [])

    def is_agent_active(self, agent_id: str) -> bool:
        return self._status.get(agent_id, "ACTIVE") == "ACTIVE"

    def sign_payload(self, agent_id: str, payload_data: Any) -> str:
        """Sign payload content with agent's private key."""
        if isinstance(payload_data, (dict, list)):
            canonical_bytes = json.dumps(payload_data, sort_keys=True, default=str).encode("utf-8")
        elif isinstance(payload_data, str):
            canonical_bytes = payload_data.encode("utf-8")
        else:
            canonical_bytes = bytes(payload_data)

        if agent_id not in self._private_keys:
            # Fallback initialization for unknown agents
            seed = f"secret_key_{agent_id}"
            if HAS_CRYPTOGRAPHY:
                seed_bytes = hashlib.sha256(seed.encode("utf-8")).digest()
                self._private_keys[agent_id] = ed25519.Ed25519PrivateKey.from_private_bytes(seed_bytes)
            else:
                self._private_keys[agent_id] = seed.encode("utf-8")

        priv_key = self._private_keys[agent_id]
        if HAS_CRYPTOGRAPHY and isinstance(priv_key, ed25519.Ed25519PrivateKey):
            sig_bytes = priv_key.sign(canonical_bytes)
            return base64.b64encode(sig_bytes).decode("utf-8")
        else:
            sig = hmac.new(priv_key, canonical_bytes, hashlib.sha256).hexdigest()
            return f"HMAC:{sig}"

    def verify_signature(self, agent_id: str, payload_data: Any, signature: str) -> bool:
        """Verify message signature against agent's registered key."""
        if not signature:
            return False

        if isinstance(payload_data, (dict, list)):
            canonical_bytes = json.dumps(payload_data, sort_keys=True, default=str).encode("utf-8")
        elif isinstance(payload_data, str):
            canonical_bytes = payload_data.encode("utf-8")
        else:
            canonical_bytes = bytes(payload_data)

        priv_key = self._private_keys.get(agent_id)
        if not priv_key:
            return False

        try:
            if HAS_CRYPTOGRAPHY and isinstance(priv_key, ed25519.Ed25519PrivateKey):
                pub_key = priv_key.public_key()
                sig_bytes = base64.b64decode(signature.encode("utf-8"))
                pub_key.verify(sig_bytes, canonical_bytes)
                return True
            else:
                expected_sig = self.sign_payload(agent_id, payload_data)
                return hmac.compare_digest(expected_sig, signature)
        except Exception as e:
            logger.warning(f"Signature verification failed for {agent_id}: {e}")
            return False

    def verify_freshness(self, timestamp_iso: str, nonce: str, max_age_seconds: int = 300) -> Tuple[bool, str]:
        """Validate timestamp age and nonce reuse to prevent replay attacks."""
        if nonce in self._used_nonces:
            return False, "REPLAY_ATTEMPT_DETECTED: Nonce already used."

        try:
            msg_dt = datetime.fromisoformat(timestamp_iso)
            now_dt = datetime.now(timezone.utc)
            if msg_dt.tzinfo is None:
                msg_dt = msg_dt.replace(tzinfo=timezone.utc)

            age = abs((now_dt - msg_dt).total_seconds())
            if age > max_age_seconds:
                return False, f"EXPIRED_TIMESTAMP: Message age ({age:.1f}s) exceeds max limit ({max_age_seconds}s)."

            self._used_nonces.add(nonce)
            # Cap nonce set size
            if len(self._used_nonces) > 10000:
                self._used_nonces.clear()

            return True, "FRESH"
        except Exception as e:
            return False, f"INVALID_TIMESTAMP_FORMAT: {e}"

# Global identity registry instance
identity_registry = AgentIdentityRegistry()
