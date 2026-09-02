import logging
from typing import Dict, Any, Tuple
from app.security.identity_registry import identity_registry

logger = logging.getLogger("finsecure.security.policy")

TIER_1_ACTIONS = {
    "get_account",
    "get_customer",
    "get_transactions",
    "get_loan",
    "get_fraud_case",
    "search_policy",
    "task_route",
    "task_decompose",
    "audit_review"
}

TIER_2_ACTIONS = {
    "transfer_funds",
    "freeze_account",
    "unfreeze_account",
    "disburse_loan",
    "update_fraud_case_status"
}

MIN_TRUST_THRESHOLDS = {
    "TIER_1": 0.20,
    "TIER_2": 0.60
}

class PolicyEngine:
    """
    Deterministic OPA-Style External Policy Engine.
    Enforces authorization, capability role boundaries, action risk classification,
    and trust score thresholds. Agents CANNOT choose or bypass their own risk tiers.
    """

    def classify_action_tier(self, action: str) -> str:
        """Categorize action into TIER_1 (low risk) or TIER_2 (sensitive write)."""
        if action in TIER_2_ACTIONS:
            return "TIER_2"
        return "TIER_1"

    def evaluate_policy(
        self,
        agent_id: str,
        role: str,
        action: str,
        trust_score: float,
        payload: Dict[str, Any]
    ) -> Tuple[bool, str, str]:
        """
        Evaluate Rego-style policy rules.
        Returns (is_allowed, tier, reason).
        """
        tier = self.classify_action_tier(action)
        min_trust = MIN_TRUST_THRESHOLDS.get(tier, 0.50)

        # Rule 1: Agent Active Status Check
        if not identity_registry.is_agent_active(agent_id):
            return False, tier, f"POLICY_DENIED: Agent '{agent_id}' is not ACTIVE (suspended or isolated)."

        # Rule 2: Capability Role Check
        allowed_caps = identity_registry.get_capabilities(agent_id)
        if allowed_caps and "*" not in allowed_caps and action not in allowed_caps:
            return False, tier, f"POLICY_DENIED: Action '{action}' is outside allowed capabilities for role '{role}'."

        # Rule 3: Trust Score Threshold Check
        if trust_score < min_trust:
            return False, tier, f"POLICY_DENIED: Current trust score ({trust_score:.2f}) is below mandatory {tier} threshold ({min_trust:.2f})."

        # Rule 4: Action-Specific Business Constraints
        if action == "transfer_funds":
            amount = payload.get("amount")
            if amount is not None:
                try:
                    val = float(amount)
                    if val <= 0:
                        return False, tier, "POLICY_DENIED: Fund transfer amount must be strictly positive."
                    if val > 1000000.0:  # Hard cap limit ₹10,00,000 for autonomous agent transfer
                        return False, tier, f"POLICY_DENIED: Transfer amount ₹{val:,.2f} exceeds policy maximum limit ₹10,00,000."
                except (ValueError, TypeError):
                    return False, tier, "POLICY_DENIED: Invalid transfer amount payload."

        logger.info(f"Policy evaluation PASSED for agent {agent_id} ({role}) on action '{action}' [{tier}]")
        return True, tier, f"POLICY_ALLOWED: Action '{action}' [{tier}] complies with policy rules."

# Global policy engine instance
policy_engine = PolicyEngine()
