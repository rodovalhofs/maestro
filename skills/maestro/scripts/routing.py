#!/usr/bin/env python3
"""P0-P3 routing decisions for maestro skill matches."""

from __future__ import annotations

import re
from typing import Any

AUTO_LOAD_CONFIDENCE = 0.22
OPTIONAL_LOAD_CONFIDENCE = 0.12
REFERENCE_BM25_SCORE = 8.0

HIGH_RISK_PATTERNS = [
    r"config\b", r"\.env", r"auth", r"delete", r"remove", r"rm\s",
    r"push\s+--force", r"deploy", r"secret", r"password", r"token",
    r"excluir", r"remover", r"deletar", r"deploy", r"producao", r"produção",
    r"\bPOST\b", r"\bPUT\b", r"\bDELETE\b",
]

VALID_MODES = {"auto-load", "recommend", "bypass"}


def bm25_to_confidence(score: float) -> float:
    """Map BM25 score to 0-1 confidence without external calibration."""
    if score <= 0:
        return 0.0
    return min(1.0, score / REFERENCE_BM25_SCORE)


def is_high_risk(task: str) -> bool:
    task_lower = task.lower()
    return any(re.search(pat, task_lower, re.IGNORECASE) for pat in HIGH_RISK_PATTERNS)


def select_mode(
    confidence: float,
    high_risk: bool,
    suggested_mode: str = "",
    bypass: bool = False,
) -> str:
    if bypass:
        return "bypass"
    if high_risk:
        return "recommend"
    if suggested_mode in VALID_MODES:
        return suggested_mode
    if confidence >= AUTO_LOAD_CONFIDENCE:
        return "auto-load"
    if confidence >= OPTIONAL_LOAD_CONFIDENCE:
        return "recommend"
    return "recommend"


def build_routing(
    task: str,
    matches: list[dict[str, Any]],
    high_risk: bool,
    bypass: bool = False,
) -> dict[str, Any]:
    if bypass or not matches:
        return {
            "priority": "P3",
            "decision": "bypass",
            "reason": "Simple or answer-only task; proceed without skill routing.",
            "load_limit": 0,
            "report_policy": "silent",
        }

    if high_risk:
        return {
            "priority": "P0",
            "decision": "recommend",
            "reason": "High-risk task; confirm before side effects.",
            "load_limit": 1,
            "report_policy": "report",
        }

    top = matches[0]
    confidence = float(top.get("confidence", 0))
    mode = str(top.get("mode", "recommend"))

    if mode == "auto-load" and confidence >= AUTO_LOAD_CONFIDENCE:
        return {
            "priority": "P1",
            "decision": "auto-load",
            "reason": "Strong workflow match.",
            "load_limit": 3,
            "report_policy": "silent",
        }

    if confidence >= OPTIONAL_LOAD_CONFIDENCE:
        return {
            "priority": "P2",
            "decision": "optional-load",
            "reason": "Medium confidence; use skill only if it changes execution.",
            "load_limit": 2,
            "report_policy": "silent",
        }

    return {
        "priority": "P3",
        "decision": "bypass",
        "reason": "No strong installed skill match.",
        "load_limit": 0,
        "report_policy": "silent",
    }
