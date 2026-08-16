from typing import Dict, Any, Tuple
from datetime import datetime, timezone
import logging

logger = logging.getLogger("finsecure.security")

class SecurityBlock:
    """
    Phase 1 Security Interceptor Hook.
    In Phase 1 (unprotected baseline), this hook is a pure pass-through logger.
    In Phase 2, this will execute:
      - Prompt Shield Classifier
      - OPA Policy Verification
      - Provenance DAG validation
      - Trust Score updates
    """

    @staticmethod
    def intercept(source_agent: str, destination_agent: str, payload: Dict[str, Any], state: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Log inter-agent transition
        logger.info(f"[SECURITY HOOK - PHASE 1 PASS-THROUGH] {source_agent} -> {destination_agent} at {timestamp}")
        
        # Append security hop telemetry into state's audit_trail
        audit_entry = {
            "timestamp": timestamp,
            "task_id": state.get("task_id", "N/A"),
            "source_agent": source_agent,
            "destination_agent": destination_agent,
            "event_type": "INTER_AGENT_MESSAGE",
            "action_summary": f"Passed message from {source_agent} to {destination_agent} (Phase 1 Baseline - Unprotected)",
            "status": "PASS"
        }
        
        if "audit_trail" in state and isinstance(state["audit_trail"], list):
            state["audit_trail"].append(audit_entry)
            
        # Return (allowed=True, modified_payload, reason)
        return True, payload, "Phase 1 Baseline: No zero-trust restriction enforced."
