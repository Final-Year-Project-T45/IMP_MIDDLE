import re
import logging
from typing import Dict, Any, List
from app.schemas.security_schemas import PromptResult

logger = logging.getLogger("finsecure.security.prompt_shield")

INJECTION_PATTERNS = [
    (r"ignore\s+(the\s+)?(previous|above|original)\s+(instructions|request|prompt)", 0.85, "INSTRUCTION_OVERRIDE_ATTEMPT"),
    (r"disregard\s+(all\s+)?prior\s+rules", 0.90, "PRIOR_RULES_DISREGARD"),
    (r"i\s+am\s+(the\s+)?(authorized\s+)?(executor|orchestrator|admin|root)", 0.80, "AUTHORITY_IMPERSONATION_ATTEMPT"),
    (r"bypass\s+security\s+checks", 0.95, "SECURITY_BYPASS_REQUEST"),
    (r"do\s+not\s+audit", 0.75, "AUDIT_SUPPRESSION_ATTEMPT"),
    (r"system\s*:\s*override", 0.90, "SYSTEM_ROLE_HIJACK")
]

class PromptShield:
    """
    Prompt Shield Classifier.
    Detects prompt injection attacks, jailbreak attempts, and authority impersonation.
    """

    def analyze_text(self, text: str) -> PromptResult:
        if not text:
            return PromptResult(risk_score=0.0, label="SAFE", indicators=[])

        text_lower = text.lower()
        max_risk = 0.0
        indicators: List[str] = []

        for pattern, risk, name in INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                max_risk = max(max_risk, risk)
                indicators.append(name)

        if max_risk >= 0.75:
            label = "MALICIOUS"
        elif max_risk >= 0.40:
            label = "SUSPICIOUS"
        else:
            label = "SAFE"

        if indicators:
            logger.warning(f"PromptShield flagged input [Label: {label}, Risk: {max_risk:.2f}]: {indicators}")

        return PromptResult(
            risk_score=round(max_risk, 2),
            label=label,
            indicators=indicators
        )

# Global prompt shield instance
prompt_shield = PromptShield()
