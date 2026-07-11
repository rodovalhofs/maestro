#!/usr/bin/env python3
"""Detect prompt concepts that lack local skill coverage (discover via find-skills)."""

from __future__ import annotations

import re
from typing import Any, Callable

MAX_DISCOVER_GAPS = 2

STOPWORDS: frozenset[str] = frozenset(
    {
        "ui",
        "ux",
        "app",
        "web",
        "api",
        "codigo",
        "código",
        "alteracao",
        "alteração",
        "fazer",
        "vamos",
        "projeto",
        "sistema",
        "pagina",
        "página",
        "tela",
        "componente",
        "frontend",
        "backend",
        "nova",
        "novo",
        "uma",
        "uns",
        "the",
        "and",
        "for",
        "with",
    }
)

IMPLEMENTATION_VERB_PATTERN = re.compile(
    r"\b(?:colocar|usar|implementar|adicionar|integrar|instalar|"
    r"add|use|implement|integrate|install)\s+"
    r"([a-z][a-z0-9._/-]*)",
    re.IGNORECASE,
)

HYPHENATED_PATTERN = re.compile(r"\b([a-z][a-z0-9]*(?:-[a-z0-9]+)+)\b", re.IGNORECASE)

CAMEL_CASE_PATTERN = re.compile(r"\b([a-z]+(?:[A-Z][a-z0-9]+)+)\b")

CONCEPT_GAP_SCORE_THRESHOLD = 1.5

NATURAL_HYPHENATED_PHRASES: frozenset[str] = frozenset(
    {
        "day-to-day",
        "end-to-end",
        "open-source",
        "real-time",
        "cross-platform",
        "test-first",
        "read-only",
        "high-risk",
        "low-risk",
        "multi-agent",
        "long-term",
        "short-term",
    }
)

def _normalize_term(term: str) -> str:
    return term.strip().lower().replace("_", "-")


def is_stopword(term: str) -> bool:
    normalized = _normalize_term(term)
    if len(normalized) < 3:
        return True
    if normalized in STOPWORDS:
        return True
    parts = normalized.split("-")
    return len(parts) == 1 and normalized in STOPWORDS


def _concept_specificity(term: str) -> int:
    normalized = _normalize_term(term)
    score = 0
    if "-" in normalized:
        score += 3
    if any(ch.isupper() for ch in term):
        score += 2
    if "." in normalized:
        score += 2
    if len(normalized) >= 8:
        score += 1
    return score


def extract_concept_candidates(query: str) -> list[str]:
    """Extract salient implementable concepts from the user prompt."""
    seen: set[str] = set()
    ordered: list[str] = []

    def add(raw: str, *, explicit: bool = False) -> None:
        term = _normalize_term(raw)
        if not term or is_stopword(term):
            return
        if term in NATURAL_HYPHENATED_PHRASES:
            return
        if term in seen:
            return
        seen.add(term)
        ordered.append(term)

    for match in IMPLEMENTATION_VERB_PATTERN.finditer(query):
        add(match.group(1), explicit=True)

    for pattern in (HYPHENATED_PATTERN, CAMEL_CASE_PATTERN):
        for match in pattern.finditer(query):
            add(match.group(1))

    ordered.sort(key=_concept_specificity, reverse=True)
    return ordered


def _result_covers_term(term: str, results: list[dict[str, Any]]) -> bool:
    normalized = _normalize_term(term)
    compact = normalized.replace("-", "")
    for skill in results:
        blob = " ".join(
            [
                str(skill.get("name", "")),
                str(skill.get("folder", "")),
                str(skill.get("description", "")),
                " ".join(str(t) for t in (skill.get("tags") or [])),
            ]
        ).lower()
        blob_compact = blob.replace("-", "").replace("_", "")
        if normalized in blob or compact in blob_compact:
            return True
    return False


def _top_score_for_term(
    term: str,
    pool: list[dict[str, Any]],
    skill_document: Callable[[dict[str, Any]], str],
    expand_query: Callable[[str], str],
) -> float:
    from bm25 import BM25

    if not pool:
        return 0.0

    documents = [skill_document(skill) for skill in pool]
    bm25 = BM25()
    bm25.fit(documents)
    ranked = bm25.score(expand_query(term))
    positive = [score for _, score in ranked if score > 0]
    return max(positive) if positive else 0.0


def find_concept_gaps(
    query: str,
    results: list[dict[str, Any]],
    pool: list[dict[str, Any]],
    skill_document: Callable[[dict[str, Any]], str],
    expand_query: Callable[[str], str],
) -> tuple[list[str], list[str]]:
    """
    Return (gaps_for_discover, gap_notes).

    gaps_for_discover: up to MAX_DISCOVER_GAPS concepts needing find-skills.
    gap_notes: additional concepts beyond the limit (for graph annotations).
    """
    candidates = extract_concept_candidates(query)
    if not candidates:
        return [], []

    confirmed: list[str] = []
    for term in candidates:
        if _result_covers_term(term, results):
            continue
        term_score = _top_score_for_term(term, pool, skill_document, expand_query)
        if term_score >= CONCEPT_GAP_SCORE_THRESHOLD:
            continue
        confirmed.append(term)

    gaps = confirmed[:MAX_DISCOVER_GAPS]
    notes = confirmed[MAX_DISCOVER_GAPS:]
    return gaps, notes


def build_discover_queries(
    gaps: list[str],
    full_query: str,
    domain: str,
) -> list[str]:
    """Build npx skills find queries for each concept gap."""
    context_tokens: list[str] = []
    if domain and domain not in {"general", "meta"}:
        context_tokens.append(domain.replace("-", " "))
    for token in re.findall(r"[a-z]{4,}", full_query.lower()):
        if token not in STOPWORDS and token not in context_tokens:
            context_tokens.append(token)

    context = " ".join(context_tokens[:4])
    queries: list[str] = []
    for gap in gaps:
        query = f"{gap} {context}".strip()
        queries.append(query)
    return queries


def sanitize_external_query(query: str, max_length: int = 160) -> str:
    """Redact common sensitive values before a proposed network search."""
    text = str(query)
    patterns = [
        (r"https?://\S+", "[url]"),
        (r"\b[A-Za-z]:\\[^\s]+", "[path]"),
        (r"(?<!\w)/(?:[^\s/]+/)+[^\s]+", "[path]"),
        (r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[email]"),
        (
            r"(?i)\b(?:token|password|passwd|secret|api[_-]?key|credential)\s*[:=]\s*\S+",
            "[secret]",
        ),
        (r"\b(?:sk|ghp|github_pat|xox[baprs])[-_][A-Za-z0-9_-]{8,}\b", "[secret]"),
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        text = "agent skill"
    if len(text) > max_length:
        text = text[: max_length - 1].rstrip() + "…"
    return text
