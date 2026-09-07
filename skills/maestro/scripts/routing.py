"""Retrieval policy. Metadata scores are evidence, never calibrated confidence."""
from __future__ import annotations

import re
import unicodedata
from typing import Any

HIGH_RISK_PATTERNS = [
    r"\bauth(?:entication|orization)?\b", r"\bdelete\b", r"\bremove\b",
    r"(?:^|\s)rm\s", r"\bpush\s+--force\b", r"\bdeploy\b",
    r"\bsecret\b", r"\bpassword\b", r"\btoken\b", r"\bexcluir\b",
    r"\bremover\b", r"\bdeletar\b", r"\bproducao\b", r"\bpublish\b",
]


def is_high_risk(task: str) -> bool:
    normalized = "".join(c for c in unicodedata.normalize("NFKD", task.casefold())
                         if not unicodedata.combining(c))
    return any(re.search(pattern, normalized) for pattern in HIGH_RISK_PATTERNS)


def select_mode(score: float, high_risk: bool, suggested_mode: str = "",
                bypass: bool = False) -> str:
    # Kept as an adapter for callers; a retrieval score never authorizes loading.
    return "bypass" if bypass else "recommend"


def build_routing(task: str, matches: list[dict[str, Any]], high_risk: bool,
                  bypass: bool = False) -> dict[str, Any]:
    margin = None
    if len(matches) > 1 and matches[0].get("score", 0) > 0:
        margin = (matches[0]["score"] - matches[1]["score"]) / matches[0]["score"]
    ambiguous = margin is not None and margin < 0.15
    if bypass:
        priority, decision, reason = "P3", "bypass", "Self-contained answer-only task."
    elif not matches:
        priority = "P0" if high_risk else "P3"
        decision, reason = "no-match", "No local metadata match; assess the gap before discovery."
    else:
        priority = "P0" if high_risk else ("P2" if ambiguous else "P1")
        decision = "compare-candidates" if ambiguous else "review-candidates"
        reason = ("Close alternatives; compare their instructions and project context."
                  if ambiguous else "Read candidate instructions before selecting skills.")
    return {
        "priority": priority, "decision": decision, "reason": reason,
        "load_limit": 0, "review_limit": 0 if bypass else min(5, len(matches)),
        "report_policy": "silent" if bypass else "report",
        "score_kind": "uncalibrated_retrieval_score",
        "requires_content_review": bool(matches) and not bypass,
        "relative_margin": round(margin, 4) if margin is not None else None,
        "ambiguous": ambiguous and not bypass,
        "question_policy": "ask_only_if_content_review_leaves_a_selection_changing_unknown",
        "execution_authorized": False,
    }
