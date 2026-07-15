#!/usr/bin/env python3
"""Batch route decomposed tasks using the fast manifest-based search engine."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from search_skills import (  # noqa: E402
    DEFAULT_MANIFEST,
    configure_stdout_utf8,
    load_manifest,
    search_skills,
)
from domains import DOMAINS  # noqa: E402


def route_batch(
    tasks: list[str],
    manifest_path: Path,
    domain: str | None = None,
) -> dict:
    manifest = load_manifest(manifest_path)
    results = [
        search_skills(task.strip(), manifest, domain=domain)
        for task in tasks
        if task.strip()
    ]

    all_gaps: list[str] = []
    all_gap_notes: list[str] = []
    discover_triggered = False
    for result in results:
        discover = result.get("discover", {})
        if discover.get("triggered"):
            discover_triggered = True
        for gap in discover.get("gaps", []):
            if gap not in all_gaps:
                all_gaps.append(gap)
        for note in discover.get("gap_notes", []):
            if note not in all_gap_notes:
                all_gap_notes.append(note)

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
        "discover": {
            "triggered": discover_triggered,
            "gaps": all_gaps,
            "gap_notes": all_gap_notes,
        },
    }


def main() -> int:
    configure_stdout_utf8()
    parser = argparse.ArgumentParser(description="Route decomposed tasks to skills")
    parser.add_argument(
        "tasks",
        nargs="*",
        help="Task strings; omit and use stdin for batch mode",
    )
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--domain", default=None, choices=DOMAINS)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.tasks:
        tasks = args.tasks
    else:
        tasks = [line.strip() for line in sys.stdin if line.strip()]

    payload = route_batch(tasks, Path(args.manifest), domain=args.domain)

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
