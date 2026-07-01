#!/usr/bin/env python3
"""Hybrid BM25 + intent routing search for maestro (manifest-only, fast)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from bm25 import BM25  # noqa: E402
from concept_gaps import build_discover_queries, find_concept_gaps  # noqa: E402
from domains import DOMAINS, HUB_SKILLS, classify_query, domain_label  # noqa: E402
from intents import apply_intent_boost, is_bypass_task, is_force_discover, task_intents  # noqa: E402
from routing import (  # noqa: E402
    bm25_to_confidence,
    build_routing,
    is_high_risk,
    select_mode,
)
from synonyms import expand_query  # noqa: E402

CURSOR_HOME = Path(os.environ.get("CURSOR_HOME", Path.home() / ".cursor"))
DEFAULT_MANIFEST = CURSOR_HOME / "skills-manifest.json"
WEAK_SCORE_THRESHOLD = 1.5
WEAK_SPREAD_RATIO = 0.10
DEFAULT_MAX_RESULTS = 5


def load_manifest(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(
            f"Manifest not found: {path}. Run: python build_manifest.py"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def skill_document(skill: dict[str, Any]) -> str:
    tags = skill.get("tags") or []
    tag_text = " ".join(str(t) for t in tags) if isinstance(tags, list) else str(tags)
    return (
        f"{skill['name']} {skill.get('folder', '')} "
        f"{skill.get('description', '')} {tag_text} {skill.get('domain', '')}"
    )


def build_discover(
    query: str,
    results: list[dict[str, Any]],
    pool: list[dict[str, Any]],
    *,
    weak: bool,
    force_discover: bool,
    bypass: bool,
    domain: str,
) -> dict[str, Any]:
    if bypass:
        return {
            "triggered": False,
            "reasons": [],
            "force_discover": False,
            "gaps": [],
            "gap_notes": [],
            "queries": [],
            "local_fallback": None,
        }

    gaps, gap_notes = find_concept_gaps(
        query, results, pool, skill_document, expand_query
    )

    reasons: list[str] = []
    if force_discover:
        reasons.append("force_discover")
    if weak:
        reasons.append("weak_match")
    if len(results) == 1 and (
        weak or results[0]["score"] < WEAK_SCORE_THRESHOLD
    ):
        reasons.append("single_local_skill")
    if gaps:
        reasons.append("concept_gap")

    triggered = bool(reasons)
    queries: list[str] = []
    if gaps:
        queries = build_discover_queries(gaps, query, domain)
    elif triggered:
        queries = [query]

    local_fallback: dict[str, str] | None = None
    if results:
        local_fallback = {
            "name": str(results[0]["name"]),
            "path": str(results[0].get("path", "")),
        }

    return {
        "triggered": triggered,
        "reasons": reasons,
        "force_discover": force_discover,
        "gaps": gaps,
        "gap_notes": gap_notes,
        "queries": queries,
        "local_fallback": local_fallback,
    }


def search_skills(
    query: str,
    manifest: dict,
    domain: str | None = None,
    max_results: int = DEFAULT_MAX_RESULTS,
    include_hubs: bool = True,
) -> dict:
    skills = manifest.get("skills", [])
    if not skills:
        return {"error": "empty_manifest", "query": query}

    bypass = is_bypass_task(query)
    high_risk = is_high_risk(query)
    force_discover = is_force_discover(query)
    intents = task_intents(query)
    expanded_query = expand_query(query)

    detected_domain, domain_scores = classify_query(query)
    active_domain = domain or detected_domain

    pool = skills
    if active_domain != "general":
        domain_pool = [s for s in skills if s.get("domain") == active_domain]
        if len(domain_pool) >= 3:
            pool = domain_pool

    documents = [skill_document(s) for s in pool]
    bm25 = BM25()
    bm25.fit(documents)
    ranked = bm25.score(expanded_query)

    results: list[dict[str, Any]] = []
    for idx, score in ranked:
        if score <= 0:
            continue
        skill = pool[idx]
        if not include_hubs and skill["name"] in HUB_SKILLS:
            continue

        skill_text = skill_document(skill)
        adjusted, intent_boosts, suggested_mode = apply_intent_boost(
            score, skill["name"], skill_text, intents
        )
        confidence = bm25_to_confidence(adjusted)
        mode = select_mode(confidence, high_risk, suggested_mode, bypass=bypass)

        entry: dict[str, Any] = {
            **skill,
            "score": round(adjusted, 4),
            "bm25_score": round(score, 4),
            "confidence": round(confidence, 3),
            "mode": mode,
            "installed": True,
        }
        if intent_boosts:
            entry["intent_boosts"] = intent_boosts
        results.append(entry)

    results.sort(key=lambda item: item["score"], reverse=True)
    results = results[:max_results]

    routing = build_routing(query, results, high_risk, bypass=bypass)

    weak = False
    weak_reasons: list[str] = []
    if not results and not bypass:
        weak = True
        weak_reasons.append("no_results")
    elif results:
        top = results[0]["score"]
        if top < WEAK_SCORE_THRESHOLD:
            weak = True
            weak_reasons.append("low_top_score")
        if len(results) >= 3:
            third = results[2]["score"]
            if top > 0 and (top - third) / top < WEAK_SPREAD_RATIO:
                weak = True
                weak_reasons.append("tight_spread")

    discover = build_discover(
        query,
        results,
        pool,
        weak=weak,
        force_discover=force_discover,
        bypass=bypass,
        domain=active_domain,
    )

    return {
        "query": query,
        "expanded_query": expanded_query,
        "domain": active_domain,
        "domain_label": domain_label(active_domain),
        "detected_domain": detected_domain,
        "domain_scores": domain_scores,
        "available_domains": DOMAINS,
        "weak_match": weak,
        "weak_reasons": weak_reasons,
        "high_risk": high_risk,
        "routing": routing,
        "count": len(results),
        "results": results,
        "discover": discover,
    }


def format_text(payload: dict) -> str:
    if "error" in payload:
        return f"Error: {payload['error']}"

    routing = payload.get("routing", {})
    lines = [
        f"Domain: {payload['domain_label']} ({payload['domain']})",
        f"Query: {payload['query']}",
        f"Routing: {routing.get('priority')} / {routing.get('decision')}",
        f"Weak match: {payload['weak_match']}",
    ]
    if payload.get("weak_reasons"):
        lines.append(f"Weak reasons: {', '.join(payload['weak_reasons'])}")

    discover = payload.get("discover", {})
    if discover.get("triggered"):
        lines.append(f"Discover: {', '.join(discover.get('reasons', []))}")
        if discover.get("gaps"):
            lines.append(f"Concept gaps: {', '.join(discover['gaps'])}")
        if discover.get("queries"):
            lines.append(f"Find queries: {', '.join(discover['queries'])}")

    lines.append("")
    for i, skill in enumerate(payload.get("results", []), 1):
        lines.append(
            f"{i}. {skill['name']} (score={skill['score']}, "
            f"confidence={skill.get('confidence')}, mode={skill.get('mode')})"
        )
        lines.append(f"   path: {skill['path']}")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Search skills for maestro")
    parser.add_argument("query", help="User prompt to match against skills")
    parser.add_argument("--domain", default=None, choices=DOMAINS)
    parser.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    manifest = load_manifest(Path(args.manifest))
    payload = search_skills(
        args.query,
        manifest,
        domain=args.domain,
        max_results=args.max_results,
    )

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(format_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
