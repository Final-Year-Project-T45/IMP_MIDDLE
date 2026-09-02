import math
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("finsecure.security.trust")

class BehavioralTrustEngine:
    """
    Behavioral Trust Engine with Non-Linear Trust Adaptation.
    Implements non-linear decay for security anomalies and controlled, resistant
    recovery to prevent reputation laundering attacks.
    """

    def __init__(self, alpha: float = 0.8, beta: float = 1.5, gamma: float = 0.05, eta_0: float = 1.0, k: float = 2.0):
        self.alpha = alpha     # Base penalty factor
        self.beta = beta       # Severe anomaly multiplier
        self.gamma = gamma     # Base recovery rate
        self.eta_0 = eta_0     # Baseline recovery resistance
        self.k = k             # Rapid recovery resistance multiplier

        # Memory store for active trust scores by agent_id
        self._trust_scores: Dict[str, float] = {
            "AGENT-ORCHESTRATOR": 1.0,
            "AGENT-PLANNER": 1.0,
            "AGENT-RESEARCHER": 1.0,
            "AGENT-EXECUTOR": 1.0,
            "AGENT-AUDITOR": 1.0,
        }
        self._recent_recovery_counts: Dict[str, int] = {}

    def get_trust(self, agent_id: str) -> float:
        """Retrieve current trust score for agent_id in [0.0, 1.0]."""
        return round(self._trust_scores.get(agent_id, 1.0), 4)

    def update_trust_event(self, agent_id: str, severity: float) -> Tuple[float, float, str]:
        """
        Process a security event with severity s in [0.0, 1.0].
        If s > 0, apply non-linear trust decay.
        If s == 0, apply controlled benign recovery.
        Returns (trust_before, trust_after, action_taken).
        """
        s = max(0.0, min(1.0, float(severity)))
        t_before = self.get_trust(agent_id)

        if s > 0.0:
            # Reset recovery velocity counter on anomaly
            self._recent_recovery_counts[agent_id] = 0

            # Non-linear penalty calculation
            penalty = self.alpha * (s ** 2) * (1.0 + self.beta * s)
            t_after = max(0.0, t_before * math.exp(-penalty))
            action = f"DECAY: Severity {s:.2f} reduced trust from {t_before:.2f} to {t_after:.2f}"
        else:
            # Benign operation recovery
            rec_count = self._recent_recovery_counts.get(agent_id, 0) + 1
            self._recent_recovery_counts[agent_id] = rec_count

            # Dynamic resistance slows rapid reputation rebuilding
            eta_t = self.eta_0 * (1.0 + self.k * (rec_count / 10.0))
            recovery = self.gamma * (1.0 - t_before) / eta_t
            t_after = min(1.0, t_before + recovery)
            action = f"RECOVERY: Benign action restored trust from {t_before:.2f} to {t_after:.2f}"

        t_after = round(t_after, 4)
        self._trust_scores[agent_id] = t_after
        logger.info(f"Trust update for {agent_id}: {action}")
        return t_before, t_after, action

# Global trust engine instance
trust_engine = BehavioralTrustEngine()
