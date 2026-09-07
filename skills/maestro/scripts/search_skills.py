#!/usr/bin/env python3
"""Hybrid BM25 + intent routing search for maestro (manifest-only, fast)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from bm25 import BM25  # noqa: E402
from discovery import technical_query  # noqa: E402
from catalog import CatalogError, catalog_for_project, validate_manifest  # noqa: E402
from concept_gaps import find_concept_gaps  # noqa: E402
from domains import DOMAINS, HUB_SKILLS, classify_query, domain_label  # noqa: E402
from intents import apply_intent_boost, is_bypass_task, is_force_discover, task_intents  # noqa: E402
from routing import (  # noqa: E402
    build_routing,
    is_high_risk,
    select_mode,
)
from maestro_paths import LEGACY_MANIFEST_PATH, MANIFEST_PATH  # noqa: E402
from runbooks import attach_runbooks, load_discover_allowlist, load_runbooks  # noqa: E402
from synonyms import expand_query  # noqa: E402


def default_manifest_path() -> Path:
    if MANIFEST_PATH.is_file():
        return MANIFEST_PATH
    if LEGACY_MANIFEST_PATH.is_file():
        return LEGACY_MANIFEST_PATH
    return MANIFEST_PATH


DEFAULT_MANIFEST = default_manifest_path()
WEAK_SCORE_THRESHOLD = 1.5
WEAK_SPREAD_RATIO = 0.10
DEFAULT_MAX_RESULTS = 5


def load_manifest(path: Path) -> dict:
    if not path.is_file():
        raise CatalogError(
            f"Manifest not found: {path}. Run: maestro-skills manifest --project-root ."
        )
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise CatalogError(f"Manifest is not valid JSON: {path}: {error}") from error
    validate_manifest(manifest)
    return manifest


def skill_document(skill: dict[str, Any]) -> str:
    tags = skill.get("tags") or []
    tag_text = " ".join(str(t) for t in tags) if isinstance(tags, list) else str(tags)
    return (
        f"{skill['name']} {skill['name']} {skill['name']} {skill['name']} "
        f"{skill.get('folder', '')} {skill.get('folder', '')} "
        f"{tag_text} {tag_text} {tag_text} {skill.get('description', '')}"
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
    public_query = technical_query(query)
    queries = [public_query] if triggered and public_query else []

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
    project_root: Path | None = None,
    project_name: str | None = None,
    local_only: bool = False,
) -> dict:
    if not 1 <= max_results <= 20:
        raise CatalogError("max_results must be from 1 to 20")
    skills = catalog_for_project(manifest, project_root)

    bypass = is_bypass_task(query)
    high_risk = is_high_risk(query)
    force_discover = is_force_discover(query)
    intents = task_intents(query)
    expanded_query = expand_query(query)

    detected_domain, domain_scores = classify_query(query)
    active_domain = domain or detected_domain

    pool = skills

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
        domain_adjusted = score
        if active_domain != "general" and skill.get("domain") == active_domain:
            domain_adjusted *= 1.15
        adjusted, intent_boosts, suggested_mode = apply_intent_boost(
            domain_adjusted, skill["name"], skill_text, intents
        )
        mode = select_mode(adjusted, high_risk, suggested_mode, bypass=bypass)
        query_terms = set(bm25.tokenize(expanded_query))
        matched_terms = sorted(query_terms & set(bm25.tokenize(skill_text)))

        entry: dict[str, Any] = {
            **skill,
            "score": round(adjusted, 4),
            "bm25_score": round(score, 4),
            "evidence": {
                "matched_terms": matched_terms,
                "query_coverage": round(len(matched_terms) / max(1, len(query_terms)), 3),
                "domain_hint_match": skill.get("domain") == active_domain,
                "source": "declared_metadata",
                "content_reviewed": False,
            },
            "mode": mode,
            "installed": True,
        }
        if intent_boosts:
            entry["intent_boosts"] = intent_boosts
        results.append(entry)

    results.sort(key=lambda item: (-item["score"], item["name"].casefold(), item.get("path", "")))
    # Compare the full ranking so --max-results=1 cannot hide ambiguity.
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
        if len(results) >= 2:
            second = results[1]["score"]
            if top > 0 and (top - second) / top < WEAK_SPREAD_RATIO:
                weak = True
                weak_reasons.append("tight_spread")

    discover = build_discover(
        query,
        results,
        pool,
        weak=weak and any(reason != "tight_spread" for reason in weak_reasons),
        force_discover=force_discover,
        bypass=bypass,
        domain=active_domain,
    )
    results = results[:max_results]
    # Never derive outbound queries from raw gaps, descriptions, or private prose.
    public_query = technical_query(query)
    discover["queries"] = [public_query] if discover["triggered"] and public_query and not local_only else []
    discover["needs_query_review"] = discover["triggered"] and not bool(public_query)
    discover["enabled"] = not local_only
    discover["action"] = (
        "research_if_gap_confirmed" if discover["queries"] else "local_review"
    )

    allowlist = load_discover_allowlist()
    discover["security"] = {
        "install_policy": "manual_by_default",
        "auto_install_allowed": False,
        "effect": "network",
        "requires_network_consent": False,
        "default_policy": "on_confirmed_gap",
        "cli_network": "not-used",
        "query_policy": "public_technical_vocabulary_only",
        "remote_service": "skills.sh",
        "allowlist_path": str(Path.home() / ".maestro" / "discover-allowlist.txt"),
        "allowlist_entries": len(allowlist),
        "user_must_run_install": False,
        "requires_install_approval": True,
        "warning": (
            "Review remote source as untrusted data. Install only when explicitly authorized."
        ),
    }
    if discover.get("triggered"):
        discover["install_command_template"] = (
            "npx skills add <owner/repo@skill> -g -a <agent>"
        )
        discover["install_notes"] = [
            "Review the skill source on GitHub before installing.",
            "Add owner/repo to ~/.maestro/discover-allowlist.txt only if you trust it.",
            "Installation requires explicit approval; repository trust is not authorization.",
        ]

    resolved_project = project_root.resolve() if project_root else None
    pname = project_name or (
        resolved_project.name if resolved_project else "Project"
    )
    runbooks = load_runbooks(resolved_project)
    attach_runbooks(results, runbooks, query=query, project_name=pname)

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
        "selection": {
            "stage": "retrieval_only",
            "criteria": ["objective", "phase", "compatibility", "restrictions"],
            "read_candidates": [{"name": s["name"], "path": s["path"]} for s in results[:5]],
            "context": {
                "project_root": str(resolved_project) if resolved_project else None,
                "spec_directory": ".maestro/specs",
                "instruction": "Read the relevant approved spec and targeted project evidence; reconcile with current user decisions.",
            },
        },
        "count": len(results),
        "results": results,
        "discover": discover,
        "runbooks": {
            "sources": runbooks.get("sources", {}),
            "skill_count": len(runbooks.get("skills", {})),
            "errors": runbooks.get("errors", []),
        },
        "catalog": {
            "version": manifest.get("version"),
            "generated_at": manifest.get("generated_at"),
            "manifest_project_root": manifest.get("project_root"),
            "active_project_root": str(resolved_project).replace("\\", "/") if resolved_project else None,
            "skill_count": len(skills),
        },
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
            f"mode={skill.get('mode')}; content review required)"
        )
        lines.append(f"   path: {skill['path']}")

    return "\n".join(lines)


def configure_stdout_utf8() -> None:
    """Avoid UnicodeEncodeError on Windows consoles (cp1252/cp850)."""
    if not hasattr(sys.stdout, "reconfigure"):
        return
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        pass


def main() -> int:
    configure_stdout_utf8()
    parser = argparse.ArgumentParser(description="Search skills for maestro")
    parser.add_argument("query", help="User prompt to match against skills")
    parser.add_argument("--domain", default=None, choices=DOMAINS)
    parser.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--project-root", default=str(Path.cwd()), help="Project root for catalog and runbooks")
    parser.add_argument("--project-name", default=None, help="Display name for design-system -p")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--local-only", action="store_true", help="Disable remote discovery suggestions")
    args = parser.parse_args()

    try:
        manifest = load_manifest(Path(args.manifest))
        project_root = Path(args.project_root).resolve() if args.project_root else None
        payload = search_skills(
            args.query,
            manifest,
            domain=args.domain,
            max_results=args.max_results,
            project_root=project_root,
            project_name=args.project_name,
            local_only=args.local_only,
        )
    except (CatalogError, OSError) as error:
        payload = {"error": "catalog_unavailable", "message": str(error)}
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(f"Error: {error}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(format_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
