#!/usr/bin/env python3
"""Load and merge Maestro skill runbooks (bundled, user, project)."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from maestro_paths import MAESTRO_HOME

BUNDLED_RUNBOOKS = Path(__file__).resolve().parent.parent / "skill-runbooks.json"
USER_RUNBOOKS = MAESTRO_HOME / "skill-runbooks.user.json"
PROJECT_RUNBOOKS_NAME = Path(".maestro") / "skill-runbooks.json"
DISCOVER_ALLOWLIST = MAESTRO_HOME / "discover-allowlist.txt"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _merge_skill_maps(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for name, entry in override.items():
        if name.startswith("_"):
            continue
        if name not in merged or not isinstance(entry, dict):
            merged[name] = deepcopy(entry)
            continue
        current = merged[name]
        if not isinstance(current, dict):
            merged[name] = deepcopy(entry)
            continue
        for key, value in entry.items():
            if key == "preflight" and isinstance(value, list) and isinstance(current.get("preflight"), list):
                current["preflight"] = value
            else:
                current[key] = deepcopy(value)
    return merged


def load_runbooks(project_root: Path | None = None) -> dict[str, Any]:
    bundled = _read_json(BUNDLED_RUNBOOKS)
    user = _read_json(USER_RUNBOOKS)
    project: dict[str, Any] = {}
    if project_root:
        project = _read_json(project_root.resolve() / PROJECT_RUNBOOKS_NAME)

    skills = _merge_skill_maps(
        bundled.get("skills", {}) if isinstance(bundled.get("skills"), dict) else {},
        user.get("skills", {}) if isinstance(user.get("skills"), dict) else {},
    )
    skills = _merge_skill_maps(
        skills,
        project.get("skills", {}) if isinstance(project.get("skills"), dict) else {},
    )

    return {
        "version": bundled.get("version", 1),
        "skills": skills,
        "sources": {
            "bundled": str(BUNDLED_RUNBOOKS),
            "user": str(USER_RUNBOOKS) if USER_RUNBOOKS.is_file() else None,
            "project": str(project_root.resolve() / PROJECT_RUNBOOKS_NAME)
            if project_root and (project_root.resolve() / PROJECT_RUNBOOKS_NAME).is_file()
            else None,
        },
    }


def resolve_preflight_command(
    preflight: dict[str, Any],
    *,
    skill_path: str,
    query: str,
    project_name: str,
) -> list[str]:
    skill_root = str(Path(skill_path).parent)
    scripts_dir = Path(skill_root) / "scripts"
    template_args = preflight.get("args") or []
    resolved: list[str] = []
    for arg in template_args:
        text = str(arg)
        text = text.replace("{skill_root}", skill_root)
        text = text.replace("{skill_scripts}", str(scripts_dir))
        text = text.replace("{query}", query)
        text = text.replace("{project_name}", project_name)
        resolved.append(text)
    return resolved


def attach_runbooks(
    results: list[dict[str, Any]],
    runbooks: dict[str, Any],
    *,
    query: str,
    project_name: str,
) -> None:
    skills = runbooks.get("skills", {})
    if not isinstance(skills, dict):
        return
    for entry in results:
        name = str(entry.get("name", ""))
        folder = str(entry.get("folder", ""))
        runbook = skills.get(name) or skills.get(folder)
        if not runbook:
            continue
        rb = deepcopy(runbook)
        preflights = rb.get("preflight") or []
        if isinstance(preflights, list):
            for pf in preflights:
                if not isinstance(pf, dict):
                    continue
                skill_path = str(entry.get("path", ""))
                if skill_path:
                    pf["resolved_args"] = resolve_preflight_command(
                        pf,
                        skill_path=skill_path,
                        query=query,
                        project_name=project_name,
                    )
        entry["runbook"] = rb


def load_discover_allowlist() -> list[str]:
    if not DISCOVER_ALLOWLIST.is_file():
        return []
    entries: list[str] = []
    for line in DISCOVER_ALLOWLIST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        entries.append(line.lower())
    return entries


def is_repo_allowlisted(repo_ref: str, allowlist: list[str] | None = None) -> bool:
    if allowlist is None:
        allowlist = load_discover_allowlist()
    if not allowlist:
        return False
    normalized = repo_ref.strip().lower().rstrip("/")
    for item in allowlist:
        if normalized == item or normalized.endswith(f"/{item}") or item in normalized:
            return True
    return False
