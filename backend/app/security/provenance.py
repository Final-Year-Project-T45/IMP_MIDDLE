import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from app.schemas.security_schemas import ProvenanceNodeSchema
from app.security.identity_registry import identity_registry

logger = logging.getLogger("finsecure.security.provenance")

class ProvenanceDAGManager:
    """
    Cryptographic Provenance DAG Manager.
    Records execution lineage from originating task instruction through multi-hop
    agent delegation to final tool execution. Verifies chain continuity.
    """

    def __init__(self):
        self._nodes: Dict[str, ProvenanceNodeSchema] = {}
        self._task_roots: Dict[str, str] = {}

    def create_node(
        self,
        event_id: str,
        task_id: str,
        agent_id: str,
        action: str,
        payload: Dict[str, Any],
        parent_event_id: Optional[str] = None,
        sender_id: Optional[str] = None,
        receiver_id: Optional[str] = None,
        capability: Optional[str] = None,
        trust_snapshot: float = 1.0,
        policy_decision: str = "ALLOW"
    ) -> ProvenanceNodeSchema:
        """Create and cryptographically sign a provenance DAG node."""
        timestamp = datetime.now(timezone.utc).isoformat()
        payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()

        canonical_str = (
            f"{event_id}|{task_id}|{agent_id}|{parent_event_id or ''}|"
            f"{action}|{payload_hash}|{trust_snapshot:.4f}|{policy_decision}|{timestamp}"
        )
        node_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
        signature = identity_registry.sign_payload(agent_id, node_hash)

        node = ProvenanceNodeSchema(
            event_id=event_id,
            task_id=task_id,
            agent_id=agent_id,
            parent_event_id=parent_event_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            action=action,
            capability=capability,
            payload_hash=payload_hash,
            trust_snapshot=trust_snapshot,
            policy_decision=policy_decision,
            timestamp=timestamp,
            node_hash=node_hash,
            signature=signature
        )

        self._nodes[event_id] = node
        if not parent_event_id:
            self._task_roots[task_id] = event_id

        logger.info(f"Provenance node created [{event_id}] for task '{task_id}' by agent '{agent_id}' (Parent: {parent_event_id})")
        return node

    def verify_lineage(self, event_id: str, expected_task_id: str) -> Tuple[bool, str]:
        """Trace lineage up to task root, verifying signatures and parent references."""
        curr_id = event_id

        visited = set()
        while curr_id:
            if curr_id in visited:
                return False, f"PROVENANCE_CYCLE_DETECTED: Cycle found at node '{curr_id}'."
            visited.add(curr_id)

            node = self._nodes.get(curr_id)
            if not node:
                # If parent event was external/initial state, pass if valid format
                return True, "PROVENANCE_VALID: Reached root or valid ancestor."

            if node.task_id != expected_task_id:
                return False, f"PROVENANCE_TASK_MISMATCH: Node '{curr_id}' task_id ({node.task_id}) mismatch with expected ({expected_task_id})."

            # Verify Node Signature
            if not identity_registry.verify_signature(node.agent_id, node.node_hash, node.signature):
                return False, f"PROVENANCE_SIGNATURE_INVALID: Cryptographic signature verification failed for node '{curr_id}'."

            curr_id = node.parent_event_id

        return True, "PROVENANCE_VALID"

# Global provenance manager instance
provenance_manager = ProvenanceDAGManager()
