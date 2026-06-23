#!/usr/bin/env python3
"""BM25 skill search for maestro orchestrator."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from bm25 import BM25  # noqa: E402
from domains import (  # noqa: E402
    DOMAINS,
    HUB_SKILLS,
    classify_query,
    domain_label,
)

CURSOR_HOME = Path(os.environ.get("CURSOR_HOME", Path.home() / ".cursor"))
DEFAULT_MANIFEST = CURSOR_HOME / "skills-manifest.json"
WEAK_SCORE_THRESHOLD = 1.5
WEAK_SPREAD_RATIO = 0.10
DEFAULT_MAX_RESULTS = 5


def load_manifest(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(
            f"Manifest not found: {path}. Run: python build-manifest.py"
        )
    return json.loads(path.read_text(encoding="utf-8"))


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

    detected_domain, domain_scores = classify_query(query)
    active_domain = domain or detected_domain

    pool = skills
    if active_domain != "general":
        domain_pool = [s for s in skills if s.get("domain") == active_domain]
        if len(domain_pool) >= 3:
            pool = domain_pool

    documents = [
        f"{s['name']} {s.get('folder', '')} {s.get('description', '')} {s.get('domain', '')}"
        for s in pool
    ]
    bm25 = BM25()
    bm25.fit(documents)
    ranked = bm25.score(query)

    results = []
    for idx, score in ranked:
        if score <= 0:
            continue
        skill = pool[idx]
        if not include_hubs and skill["name"] in HUB_SKILLS:
            continue
        results.append({**skill, "score": round(score, 4)})
        if len(results) >= max_results:
            break

    weak = False
    reason: list[str] = []
    if not results:
        weak = True
        reason.append("no_results")
    else:
        top = results[0]["score"]
        if top < WEAK_SCORE_THRESHOLD:
            weak = True
            reason.append("low_top_score")
        if len(results) >= 3:
            third = results[2]["score"]
            if top > 0 and (top - third) / top < WEAK_SPREAD_RATIO:
                weak = True
                reason.append("tight_spread")

    return {
        "query": query,
        "domain": active_domain,
        "domain_label": domain_label(active_domain),
        "detected_domain": detected_domain,
        "domain_scores": domain_scores,
        "available_domains": DOMAINS,
        "weak_match": weak,
        "weak_reasons": reason,
        "count": len(results),
        "results": results,
    }


def format_text(payload: dict) -> str:
    if "error" in payload:
        return f"Error: {payload['error']}"

    lines = [
        f"Domain: {payload['domain_label']} ({payload['domain']})",
        f"Query: {payload['query']}",
        f"Weak match: {payload['weak_match']}",
    ]
    if payload.get("weak_reasons"):
        lines.append(f"Weak reasons: {', '.join(payload['weak_reasons'])}")

    lines.append("")
    for i, skill in enumerate(payload.get("results", []), 1):
        lines.append(
            f"{i}. {skill['name']} (score={skill['score']}, domain={skill['domain']})"
        )
        lines.append(f"   path: {skill['path']}")
        desc = skill.get("description", "")
        if len(desc) > 160:
            desc = desc[:157] + "..."
        lines.append(f"   {desc}")

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
