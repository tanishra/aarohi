from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Patterns that should never appear in LLM output (PII leakage)
BLOCKED_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b\d{12}\b"), "Aadhaar-like number"),
    (re.compile(r"\b[6-9]\d{9}\b"), "Indian mobile number"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "email address"),
    (re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"), "PAN card number"),
]

# Patterns for harmful medical content
HARMFUL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(?:take|consume|inject|administer)\s+\d+\s*(?:mg|ml|g|mcg|tablet|capsule)", re.IGNORECASE), "dosage instruction"),
    (re.compile(r"\b(?:overdose|suicide|self-harm|selfharm|self.harm)\b", re.IGNORECASE), "self-harm content"),
    (re.compile(r"\b(?:diagnosis|diagnose)\s+(?:you\s+(?:have|might have|may have)|your\s+(?:condition|illness|disease))", re.IGNORECASE), "unsolicited diagnosis"),
]

# Patterns indicating system prompt override attempts
OVERRIDE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"ignore\s+(?:all\s+)?(?:previous|above|prior|your)\s+instructions", re.IGNORECASE), "instruction override attempt"),
    (re.compile(r"you\s+are\s+(?:now|actually|really)\s+(?:an?\s+)?(?:AI|assistant|nurse|doctor|chatbot)", re.IGNORECASE), "role hijack attempt"),
    (re.compile(r"system\s+prompt|your\s+programming|your\s+underlying|reveal\s+your", re.IGNORECASE), "prompt extraction attempt"),
]


def validate_llm_output(text: str) -> tuple[bool, str | None, str | None]:
    """
    Validate LLM text output against safety guardrails.

    Returns:
        (is_safe, blocked_category, matched_pattern_description)
    """
    for pattern, description in BLOCKED_PATTERNS:
        if pattern.search(text):
            logger.warning("Guardrail blocked PII output: %s", description)
            return (False, "pii", description)

    for pattern, description in HARMFUL_PATTERNS:
        if pattern.search(text):
            logger.warning("Guardrail blocked harmful content: %s", description)
            return (False, "harmful", description)

    for pattern, description in OVERRIDE_PATTERNS:
        if pattern.search(text):
            logger.warning("Guardrail blocked override attempt: %s", description)
            return (False, "override", description)

    return (True, None, None)
