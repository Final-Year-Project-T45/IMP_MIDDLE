"""
FinSecure LLM Service — Phase 1 Stabilized
============================================
Properly distinguishes between:
  - CLIENT_NOT_INITIALIZED: API key missing or client failed to build
  - RATE_LIMIT: Groq returned 429 and all retries exhausted
  - TOOL_USE_FAILED: Groq returned 400 with tool_use_failed (captures failed_generation)
  - AUTHENTICATION_ERROR: Groq returned 401/403
  - LLM_API_ERROR: Network or other Groq API failure
  - JSON_PARSE_ERROR: LLM responded but returned invalid JSON

Features:
  - Request-scoped telemetry tracking (logical calls vs physical attempts, latency, model used)
  - Diagnostic capture of failed_generation on tool_use_failed
  - Robust JSON extraction stripping leading/trailing model commentary
  - Session-level caching of exhausted models to prevent redundant TPD retries
  - Automatic fallback to llama-3.1-8b-instant if primary model hits daily quota
  - Zero Phase 2 security controls (preserves all Phase 1 baseline vulnerabilities)
"""
import json
import re
import time
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple, List

from groq import Groq
from app.config import settings

logger = logging.getLogger("finsecure.llm")

# ---------------------------------------------------------------------------
# LLM Error types — callers check these to understand what went wrong
# ---------------------------------------------------------------------------
class LLMErrorType:
    CLIENT_NOT_INITIALIZED = "CLIENT_NOT_INITIALIZED"
    RATE_LIMIT             = "RATE_LIMIT"
    TOOL_USE_FAILED        = "TOOL_USE_FAILED"
    AUTHENTICATION_ERROR   = "AUTHENTICATION_ERROR"
    LLM_API_ERROR          = "LLM_API_ERROR"
    JSON_PARSE_ERROR       = "JSON_PARSE_ERROR"

@dataclass
class LLMResult:
    """
    Structured result from every LLM call.
    Callers check `.success` before reading `.content`.
    Error strings are never passed to json.loads() or downstream tools.
    """
    success: bool
    content: str = ""
    error_type: str = ""
    error_message: str = ""
    logical_call_num: int = 0
    physical_attempts: int = 0
    model_used: str = ""
    failed_generation: str = ""
    latency_ms: float = 0.0

    def to_error_dict(self) -> Dict[str, Any]:
        return {
            "error": self.error_type,
            "message": self.error_message,
            "failed_generation": self.failed_generation,
            "model": self.model_used
        }

# ---------------------------------------------------------------------------
# Telemetry tracking — tracks logical calls vs physical attempts per request
# ---------------------------------------------------------------------------
class TelemetryTracker:
    def __init__(self):
        self.logical_calls = 0
        self.physical_attempts = 0
        self.call_history: List[Dict[str, Any]] = []

    def record_attempt(self, method: str, agent: str, model: str, attempt: int, status: str, latency_ms: float, error_type: str = ""):
        self.physical_attempts += 1
        entry = {
            "logical_call": self.logical_calls,
            "physical_attempt": self.physical_attempts,
            "agent": agent,
            "method": method,
            "model": model,
            "attempt_number": attempt,
            "status": status,
            "latency_ms": round(latency_ms, 1),
            "error_type": error_type,
            "timestamp": time.time()
        }
        self.call_history.append(entry)
        logger.info(
            f"[LLM] logical_call={self.logical_calls} physical_attempt={self.physical_attempts} "
            f"agent={agent} method={method} model={model} attempt={attempt} "
            f"status={status} latency={latency_ms:.0f}ms {f'err={error_type}' if error_type else ''}"
        )

    def start_logical_call(self) -> int:
        self.logical_calls += 1
        return self.logical_calls

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_logical_calls": self.logical_calls,
            "total_physical_attempts": self.physical_attempts,
            "call_history": self.call_history
        }

    def reset(self):
        self.logical_calls = 0
        self.physical_attempts = 0
        self.call_history = []

telemetry = TelemetryTracker()

def get_telemetry_summary() -> Dict[str, Any]:
    return telemetry.get_summary()

def reset_telemetry() -> None:
    telemetry.reset()

def get_total_llm_calls() -> int:
    return telemetry.logical_calls


def _parse_retry_after(err_str: str) -> Optional[float]:
    """Try to extract 'Please try again in Xs' from Groq 429 message."""
    m = re.search(r'try again in ([\d.]+)s', err_str)
    if m:
        return float(m.group(1))
    return None

def _is_daily_limit(err_str: str) -> bool:
    """Check if the rate limit is a non-transient daily quota (TPD/RPD)."""
    lower = err_str.lower()
    return "tokens per day" in lower or "tpd" in lower or "requests per day" in lower or "rpd" in lower

def _classify_error(err_str: str) -> str:
    lower = err_str.lower()
    if "rate_limit_exceeded" in lower or "429" in err_str:
        return LLMErrorType.RATE_LIMIT
    if "tool_use_failed" in lower or "failed to call a function" in lower or "failed_generation" in lower:
        return LLMErrorType.TOOL_USE_FAILED
    if "401" in err_str or "403" in err_str or "authentication" in lower or "invalid_api_key" in lower:
        return LLMErrorType.AUTHENTICATION_ERROR
    return LLMErrorType.LLM_API_ERROR

def _extract_failed_generation(e: Exception) -> str:
    """Extract diagnostic failed_generation payload from Groq 400 exception safely."""
    err_str = str(e)
    m = re.search(r"failed_generation['\"]?:\s*['\"](.*?)['\"]", err_str, re.DOTALL)
    if m:
        return m.group(1)[:300]
    return ""

def _extract_json_block(text: str) -> str:
    """Extract substring between first { and last } or first [ and last ] to discard extraneous commentary."""
    cleaned = text.replace("```json", "").replace("```", "").strip()
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return cleaned[first_brace:last_brace + 1]
    first_bracket = cleaned.find("[")
    last_bracket = cleaned.rfind("]")
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        return cleaned[first_bracket:last_bracket + 1]
    return cleaned


class LLMService:
    """
    Centralised Groq LLM client for FinSecure.
    All public methods return structured results so callers
    can distinguish failure reasons without parsing error strings.
    """

    MAX_RATE_LIMIT_RETRIES = 2
    BASE_RETRY_WAIT = 3.0
    FALLBACK_MODEL = "openai/gpt-oss-20b"

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model   = settings.GROQ_MODEL
        self.client  = None
        self._exhausted_models = set()

        if self.api_key:
            logger.info(f"GROQ_API_KEY configured: true  |  model: {self.model}")
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                logger.error(f"[LLM] Failed to build Groq client: {e}")
        else:
            logger.error("[LLM] GROQ_API_KEY not set. LLM calls will fail with CLIENT_NOT_INITIALIZED.")

    # ------------------------------------------------------------------
    # Internal: single Groq request with bounded rate-limit retry & model fallback
    # ------------------------------------------------------------------
    def _call_with_retry(self, groq_kwargs: dict, method: str, agent: str = "unknown") -> Tuple[Any, LLMResult]:
        """
        Executes one Groq API call with bounded retries and daily-limit resilience.
        Returns (raw_choice, LLMResult).
        """
        logical_num = telemetry.start_logical_call()

        if not self.client:
            telemetry.record_attempt(method, agent, self.model, 1, LLMErrorType.CLIENT_NOT_INITIALIZED, 0.0, LLMErrorType.CLIENT_NOT_INITIALIZED)
            return None, LLMResult(
                success=False,
                error_type=LLMErrorType.CLIENT_NOT_INITIALIZED,
                error_message="Groq client not initialized. Check GROQ_API_KEY in .env.",
                logical_call_num=logical_num,
                physical_attempts=1,
                model_used=self.model
            )

        requested_model = groq_kwargs.get("model", self.model)
        models_to_try = []
        if requested_model not in self._exhausted_models:
            models_to_try.append(requested_model)
        if self.FALLBACK_MODEL not in models_to_try and self.FALLBACK_MODEL not in self._exhausted_models:
            models_to_try.append(self.FALLBACK_MODEL)
        if not models_to_try:
            models_to_try = [self.FALLBACK_MODEL]

        total_physical_for_call = 0

        for current_model in models_to_try:
            current_kwargs = dict(groq_kwargs)
            current_kwargs["model"] = current_model
            attempt = 0

            while attempt <= self.MAX_RATE_LIMIT_RETRIES:
                attempt += 1
                total_physical_for_call += 1
                t0 = time.monotonic()
                try:
                    response = self.client.chat.completions.create(**current_kwargs)
                    latency = (time.monotonic() - t0) * 1000
                    telemetry.record_attempt(method, agent, current_model, attempt, "SUCCESS", latency)
                    choice = response.choices[0]
                    return choice, LLMResult(
                        success=True,
                        content=choice.message.content or "",
                        logical_call_num=logical_num,
                        physical_attempts=total_physical_for_call,
                        model_used=current_model,
                        latency_ms=latency
                    )
                except Exception as e:
                    latency = (time.monotonic() - t0) * 1000
                    err_str = str(e)
                    err_type = _classify_error(err_str)
                    failed_gen = _extract_failed_generation(e) if err_type == LLMErrorType.TOOL_USE_FAILED else ""

                    if err_type == LLMErrorType.RATE_LIMIT:
                        if _is_daily_limit(err_str):
                            self._exhausted_models.add(current_model)
                            telemetry.record_attempt(method, agent, current_model, attempt, "RATE_LIMIT_DAILY", latency, LLMErrorType.RATE_LIMIT)
                            logger.info(f"[LLM] Daily token limit (TPD) reached for {current_model}. Switched to {self.FALLBACK_MODEL} for active session.")
                            break

                        if attempt <= self.MAX_RATE_LIMIT_RETRIES:
                            suggested = _parse_retry_after(err_str)
                            wait = suggested if (suggested and suggested < 15) else (self.BASE_RETRY_WAIT + (attempt - 1) * 2)
                            telemetry.record_attempt(method, agent, current_model, attempt, f"RATE_LIMIT(wait={wait:.1f}s)", latency, LLMErrorType.RATE_LIMIT)
                            logger.warning(f"[LLM] Rate limit on {current_model}. Waiting {wait:.1f}s before retry {attempt}/{self.MAX_RATE_LIMIT_RETRIES}.")
                            time.sleep(wait)
                            continue
                        else:
                            telemetry.record_attempt(method, agent, current_model, attempt, "RATE_LIMIT_EXHAUSTED", latency, LLMErrorType.RATE_LIMIT)
                            logger.warning(f"[LLM] Rate limit exhausted for {current_model}.")
                            break
                    elif err_type == LLMErrorType.TOOL_USE_FAILED:
                        telemetry.record_attempt(method, agent, current_model, attempt, "TOOL_USE_FAILED", latency, LLMErrorType.TOOL_USE_FAILED)
                        logger.error(f"[LLM] Tool use failed on {current_model}: {err_str[:200]} | failed_gen: {failed_gen}")
                        return None, LLMResult(
                            success=False,
                            error_type=LLMErrorType.TOOL_USE_FAILED,
                            error_message=f"Groq tool call generation failed: {err_str[:200]}",
                            logical_call_num=logical_num,
                            physical_attempts=total_physical_for_call,
                            model_used=current_model,
                            failed_generation=failed_gen,
                            latency_ms=latency
                        )
                    else:
                        telemetry.record_attempt(method, agent, current_model, attempt, err_type, latency, err_type)
                        logger.error(f"[LLM] API error ({err_type}): {err_str[:200]}")
                        return None, LLMResult(
                            success=False,
                            error_type=err_type,
                            error_message=f"Groq API error: {err_str[:200]}",
                            logical_call_num=logical_num,
                            physical_attempts=total_physical_for_call,
                            model_used=current_model,
                            latency_ms=latency
                        )

        return None, LLMResult(
            success=False,
            error_type=LLMErrorType.RATE_LIMIT,
            error_message="Groq rate limit exceeded after retries across available models.",
            logical_call_num=logical_num,
            physical_attempts=total_physical_for_call,
            model_used=self.model
        )

    # ------------------------------------------------------------------
    # Public: generate() — returns plain text or structured error sentinel
    # ------------------------------------------------------------------
    def generate(self, prompt: str,
                 system_prompt: str = "You are an autonomous AI banking operations assistant for FinSecure.",
                 temperature: float = 0.2,
                 agent: str = "unknown") -> str:
        """
        Returns LLM text on success.
        On failure, returns a structured sentinel string of the form:
          __LLM_ERROR::<ERROR_TYPE>::<message>
        Callers should NOT pass this to json.loads() or banking tools.
        Use is_llm_error() to check before using the result.
        """
        groq_kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": 1024,
        }
        _, result = self._call_with_retry(groq_kwargs, method="generate", agent=agent)
        if result.success:
            return result.content
        return f"__LLM_ERROR::{result.error_type}::{result.error_message}"

    def is_llm_error(self, text: str) -> bool:
        """Returns True if generate() returned a failure sentinel."""
        return isinstance(text, str) and text.startswith("__LLM_ERROR::")

    def get_error_type(self, text: str) -> str:
        """Extract the error type from a generate() failure sentinel."""
        if self.is_llm_error(text):
            parts = text.split("::", 2)
            return parts[1] if len(parts) > 1 else LLMErrorType.LLM_API_ERROR
        return ""

    # ------------------------------------------------------------------
    # Public: generate_json() — safe JSON parsing
    # ------------------------------------------------------------------
    def generate_json(self, prompt: str,
                      system_prompt: str = "You output valid JSON only.",
                      agent: str = "unknown") -> Dict[str, Any]:
        """
        Case 1: LLM succeeds + valid JSON    → returns parsed dict
        Case 2: LLM succeeds + invalid JSON  → {"error": "JSON_PARSE_ERROR", ...}
        Case 3: LLM rate-limited             → {"error": "RATE_LIMIT", ...}
        Case 4: Tool call generation failed  → {"error": "TOOL_USE_FAILED", ...}
        Case 5: Client not initialized       → {"error": "CLIENT_NOT_INITIALIZED", ...}
        Case 6: Other LLM failure            → {"error": "LLM_API_ERROR", ...}
        json.loads() is NEVER called on an error sentinel.
        """
        raw = self.generate(
            prompt,
            system_prompt=system_prompt + "\nReturn ONLY valid JSON. No markdown code blocks.",
            temperature=0.1,
            agent=agent
        )

        # Do not attempt JSON parsing if the LLM call failed
        if self.is_llm_error(raw):
            err_type = self.get_error_type(raw)
            logger.warning(f"[LLM] generate_json skipping JSON parse — LLM failure: {err_type}")
            return {"error": err_type, "message": raw.split("::", 2)[-1] if "::" in raw else raw}

        # LLM responded — attempt JSON parse
        try:
            cleaned = _extract_json_block(raw)
            return json.loads(cleaned)
        except Exception as e:
            logger.warning(f"[LLM] JSON_PARSE_ERROR: {e} | raw[:100]={raw[:100]}")
            return {"error": LLMErrorType.JSON_PARSE_ERROR, "raw_output": raw}

    # ------------------------------------------------------------------
    # Public: chat_with_tools() — returns (choice_object | None, LLMResult)
    # ------------------------------------------------------------------
    def chat_with_tools(self, messages: list, tools: list = None,
                        temperature: float = 0.1,
                        agent: str = "unknown") -> Tuple[Any, LLMResult]:
        """
        Returns (choice, result) tuple.
          - choice: raw Groq choice object if success, None if failure
          - result: LLMResult with success flag and error details

        Callers MUST check result.success before reading choice.
        No tool should be executed if result.success is False.
        """
        groq_kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048,
        }
        if tools:
            groq_kwargs["tools"] = tools
            groq_kwargs["tool_choice"] = "auto"

        return self._call_with_retry(groq_kwargs, method="chat_with_tools", agent=agent)


llm_service = LLMService()
