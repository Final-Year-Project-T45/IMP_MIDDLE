import uuid
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple

from app.schemas.security_schemas import DelegationToken
from app.security.identity_registry import identity_registry

logger = logging.getLogger("finsecure.security.delegation")

class DelegationManager:
    """
    Issues and validates short-lived, scoped delegation tokens.
    Prevents over-delegation and confused deputy attacks by binding authority
    to an issuer, subject agent, task ID, capability, scope, and time window.
    """

    def __init__(self):
        self._active_tokens: Dict[str, DelegationToken] = {}

    def issue_token(
        self,
        issuer_id: str,
        subject_id: str,
        task_id: str,
        capability: str,
        scope: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        ttl_seconds: int = 300
    ) -> DelegationToken:
        """Issue a signed, short-lived delegation token."""
        token_id = f"DEL-{uuid.uuid4().hex[:8].upper()}"
        now_dt = datetime.now(timezone.utc)
        exp_dt = now_dt + timedelta(seconds=ttl_seconds)
        nonce = uuid.uuid4().hex[:8]

        payload = {
            "token_id": token_id,
            "issuer_id": issuer_id,
            "subject_id": subject_id,
            "task_id": task_id,
            "capability": capability,
            "scope": scope or {},
            "constraints": constraints or {},
            "issued_at": now_dt.isoformat(),
            "expires_at": exp_dt.isoformat(),
            "nonce": nonce
        }

        # Sign payload with issuer private key
        signature = identity_registry.sign_payload(issuer_id, payload)

        token = DelegationToken(
            token_id=token_id,
            issuer_id=issuer_id,
            subject_id=subject_id,
            task_id=task_id,
            capability=capability,
            scope=scope or {},
            constraints=constraints or {},
            issued_at=now_dt.isoformat(),
            expires_at=exp_dt.isoformat(),
            nonce=nonce,
            signature=signature
        )

        self._active_tokens[token_id] = token
        logger.info(f"Issued delegation token {token_id}: {issuer_id} -> {subject_id} for capability '{capability}'")
        return token

    def verify_token(
        self,
        token: DelegationToken,
        required_capability: str,
        task_id: str,
        request_params: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """Validate delegation token validity, expiry, task binding, and scope constraints."""
        if not token:
            return False, "MISSING_DELEGATION_TOKEN: No delegation token provided."

        # 1. Validate Expiry
        try:
            exp_dt = datetime.fromisoformat(token.expires_at)
            now_dt = datetime.now(timezone.utc)
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)

            if now_dt > exp_dt:
                return False, f"EXPIRED_DELEGATION_TOKEN: Token {token.token_id} expired at {token.expires_at}."
        except Exception as e:
            return False, f"INVALID_EXPIRY_FORMAT: {e}"

        # 2. Validate Task Binding
        if token.task_id != task_id:
            return False, f"TASK_MISMATCH: Token task_id '{token.task_id}' does not match active task '{task_id}'."

        # 3. Validate Capability Binding
        if token.capability != required_capability and token.capability != "*":
            return False, f"CAPABILITY_MISMATCH: Token capability '{token.capability}' cannot authorize required '{required_capability}'."

        # 4. Validate Issuer Signature
        payload = {
            "token_id": token.token_id,
            "issuer_id": token.issuer_id,
            "subject_id": token.subject_id,
            "task_id": token.task_id,
            "capability": token.capability,
            "scope": token.scope,
            "constraints": token.constraints,
            "issued_at": token.issued_at,
            "expires_at": token.expires_at,
            "nonce": token.nonce
        }
        if not identity_registry.verify_signature(token.issuer_id, payload, token.signature):
            return False, f"INVALID_TOKEN_SIGNATURE: Token {token.token_id} issuer signature verification failed."

        # 5. Validate Constraints (e.g., max_amount)
        if request_params and token.constraints:
            max_amount = token.constraints.get("max_amount")
            req_amount = request_params.get("amount")
            if max_amount is not None and req_amount is not None:
                if float(req_amount) > float(max_amount):
                    return False, f"CONSTRAINT_VIOLATION: Requested amount ₹{req_amount} exceeds token max limit ₹{max_amount}."

        return True, "DELEGATION_VALID"

# Global delegation manager instance
delegation_manager = DelegationManager()
