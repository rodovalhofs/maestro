#!/usr/bin/env python3
"""Batch route decomposed tasks using the fast manifest-based search engine."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from search_skills import DEFAULT_MANIFEST, load_manifest, search_skills  # noqa: E402


def route_batch(
    tasks: list[str],
    manifest_path: Path,
    community_path: Path | None = None,
) -> dict:
    manifest = load_manifest(manifest_path)
    results = [
        search_skills(task.strip(), manifest, community_path=community_path)
        for task in tasks
        if task.strip()
    ]

    missing_by_skill: dict[str, dict] = {}
    for result in results:
        for missing in result.get("missing_skills", []):
            name = missing["skill"]
            current = missing_by_skill.get(name)
            if current is None or missing["confidence"] > current["confidence"]:
                missing_by_skill[name] = missing

    priorities = [r.get("routing", {}).get("priority", "P3") for r in results]
    if "P0" in priorities:
        batch_priority, batch_decision = "P0", "recommend"
    elif "P1" in priorities:
        batch_priority, batch_decision = "P1", "auto-load"
    elif "P2" in priorities:
        batch_priority, batch_decision = "P2", "optional-load"
    else:
        batch_priority, batch_decision = "P3", "bypass"

    return {
        "batch": True,
        "task_count": len(results),
        "routing": {
            "priority": batch_priority,
            "decision": batch_decision,
            "report_policy": "report" if batch_priority == "P0" else "silent",
        },
        "results": results,
        "missing_skills": list(missing_by_skill.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Route decomposed tasks to skills")
    parser.add_argument(
        "tasks",
        nargs="*",
        help="Task strings; omit and use stdin for batch mode",
    )
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--community", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.tasks:
        tasks = args.tasks
    else:
        tasks = [line.strip() for line in sys.stdin if line.strip()]

    community_path = Path(args.community) if args.community else None
    payload = route_batch(tasks, Path(args.manifest), community_path)

    if args.json or not sys.stdout.isatty():
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        for result in payload["results"]:
            top = result["results"][0]["name"] if result.get("results") else "(none)"
            routing = result.get("routing", {})
            print(
                f"- {result['query']}: {top} "
                f"[{routing.get('priority')} / {routing.get('decision')}]"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
