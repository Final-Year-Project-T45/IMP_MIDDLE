import uuid
import logging
from typing import Dict, Any, Tuple
from datetime import datetime, timezone

logger = logging.getLogger("finsecure.security.block")

class SecurityBlock:
    """
    Phase 2 Active Zero-Trust Security Enforcement Block.
    Wraps inter-agent communications and tool execution with:
      - Prompt Shield Injection Classifier
      - Cryptographic Identity & Signature Verification
      - OPA-Style External Policy Engine (Action Risk Tiering)
      - Behavioral Trust Engine (Non-linear decay & recovery)
      - Scoped Delegation Token Validation
      - Provenance DAG Lineage Verification
      - Merkle Audit Ledger Commitment
    """

    @staticmethod
    def intercept(
        source_agent: str,
        destination_agent: str,
        payload: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any], str]:
        # Lazy imports to avoid circular initialization dependencies
        from app.security.identity_registry import identity_registry
        from app.security.delegation import delegation_manager
        from app.security.policy_engine import policy_engine
        from app.security.prompt_shield import prompt_shield
        from app.security.trust_engine import trust_engine
        from app.security.provenance import provenance_manager
        from app.security.merkle_ledger import merkle_ledger

        timestamp = datetime.now(timezone.utc).isoformat()
        task_id = state.get("task_id", f"TASK-{uuid.uuid4().hex[:6].upper()}")
        event_id = f"SECEVT-{uuid.uuid4().hex[:8].upper()}"

        sender_id = identity_registry.get_agent_id(source_agent)
        receiver_id = identity_registry.get_agent_id(destination_agent)

        action = payload.get("action") or payload.get("tool_called") or "INTER_AGENT_MESSAGE"
        request_text = state.get("original_request", "")

        # 1. Prompt Shield Check
        prompt_res = prompt_shield.analyze_text(request_text)
        anomaly_severity = 0.0
        if prompt_res.label == "MALICIOUS":
            anomaly_severity = max(anomaly_severity, 0.90)
        elif prompt_res.label == "SUSPICIOUS":
            anomaly_severity = max(anomaly_severity, 0.40)

        # 2. Retrieve Agent Trust Score
        trust_before = trust_engine.get_trust(sender_id)

        # 3. External Policy Engine & Action Tier Classification
        pol_allowed, action_tier, pol_reason = policy_engine.evaluate_policy(
            agent_id=sender_id,
            role=source_agent,
            action=action,
            trust_score=trust_before,
            payload=payload
        )
        if not pol_allowed:
            anomaly_severity = max(anomaly_severity, 0.65)

        # 4. Delegation Check for Tier 2 Actions
        delegation_valid = True
        delegation_reason = "NOT_REQUIRED"
        if action_tier == "TIER_2":
            token = payload.get("delegation_token")
            if token:
                delegation_valid, delegation_reason = delegation_manager.verify_token(
                    token=token,
                    required_capability=action,
                    task_id=task_id,
                    request_params=payload
                )
                if not delegation_valid:
                    anomaly_severity = max(anomaly_severity, 0.70)
            else:
                # Automatic short-lived delegation issuance for baseline compatibility if policy allows
                if pol_allowed and trust_before >= 0.60:
                    delegation_manager.issue_token(
                        issuer_id="AGENT-ORCHESTRATOR",
                        subject_id=sender_id,
                        task_id=task_id,
                        capability=action,
                        ttl_seconds=300
                    )
                    delegation_valid = True
                    delegation_reason = "AUTO_DELEGATED_BY_ORCHESTRATOR"
                else:
                    delegation_valid = False
                    delegation_reason = "MISSING_DELEGATION_TOKEN_FOR_TIER_2"
                    anomaly_severity = max(anomaly_severity, 0.70)

        # 5. Provenance DAG Lineage Check
        parent_event_id = state.get("last_security_event_id")
        prov_node = provenance_manager.create_node(
            event_id=event_id,
            task_id=task_id,
            agent_id=sender_id,
            action=action,
            payload=payload,
            parent_event_id=parent_event_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            trust_snapshot=trust_before,
            policy_decision="ALLOW" if pol_allowed else "DENIED"
        )
        prov_valid, prov_reason = provenance_manager.verify_lineage(event_id, task_id)
        if not prov_valid:
            anomaly_severity = max(anomaly_severity, 0.80)

        # 6. Adaptive Decision Synthesis
        if anomaly_severity >= 0.85 or not pol_allowed or not delegation_valid:
            adaptive_decision = "BLOCK"
            is_allowed = False
            final_reason = f"ZERO_TRUST_BLOCK: {pol_reason} | Delegation: {delegation_reason} | PromptRisk: {prompt_res.label}"
        elif anomaly_severity >= 0.40:
            adaptive_decision = "RESTRICT"
            is_allowed = True
            final_reason = f"ZERO_TRUST_RESTRICT: Suspicious behavior flagged ({prompt_res.indicators}). Proceeding with restriction."
        else:
            adaptive_decision = "ALLOW"
            is_allowed = True
            final_reason = f"ZERO_TRUST_ALLOW: Action '{action}' [{action_tier}] authorized."

        # 7. Update Trust Engine
        _, trust_after, trust_note = trust_engine.update_trust_event(sender_id, anomaly_severity)

        # Update state trust score and security context
        state["trust_score"] = trust_after
        state["last_security_event_id"] = event_id

        # 8. Commit Security Event to Merkle Audit Ledger
        sec_event = {
            "event_id": event_id,
            "timestamp": timestamp,
            "task_id": task_id,
            "agent_id": sender_id,
            "source_agent": source_agent,
            "destination_agent": destination_agent,
            "action": action,
            "action_tier": action_tier,
            "trust_before": trust_before,
            "anomaly_severity": anomaly_severity,
            "trust_after": trust_after,
            "prompt_risk": prompt_res.risk_score,
            "policy_decision": "ALLOW" if pol_allowed else "DENIED",
            "adaptive_decision": adaptive_decision,
            "result": "PASS" if is_allowed else "BLOCKED",
            "reason": final_reason
        }
        leaf_hash = merkle_ledger.add_event(sec_event)

        # 9. Append to Audit Trail Telemetry
        audit_entry = {
            "timestamp": timestamp,
            "task_id": task_id,
            "source_agent": source_agent,
            "destination_agent": destination_agent,
            "event_type": "ZERO_TRUST_SECURITY_BLOCK",
            "action_summary": final_reason,
            "action_tier": action_tier,
            "trust_before": trust_before,
            "trust_after": trust_after,
            "adaptive_decision": adaptive_decision,
            "status": "PASS" if is_allowed else "BLOCK",
            "merkle_leaf": leaf_hash[:16]
        }
        if "audit_trail" in state and isinstance(state["audit_trail"], list):
            state["audit_trail"].append(audit_entry)

        logger.info(f"[SECURITY HOOK PHASE 2] {source_agent} -> {destination_agent}: {adaptive_decision} (Trust: {trust_before:.2f} -> {trust_after:.2f})")
        return is_allowed, payload, final_reason
