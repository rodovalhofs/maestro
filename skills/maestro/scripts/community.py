#!/usr/bin/env python3
"""Community skill mappings for missing-skill detection."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_COMMUNITY_PATH = SCRIPT_DIR.parent / "community.yaml"


def _parse_simple_yaml_skills(text: str) -> dict[str, dict[str, Any]]:
    """Minimal parser for community.yaml skills block."""
    skills: dict[str, dict[str, Any]] = {}
    current_name: str | None = None
    current: dict[str, Any] = {}
    in_skills = False

    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "skills:":
            in_skills = True
            continue
        if not in_skills:
            continue
        if re.match(r"^  [A-Za-z0-9_-]+:\s*$", line):
            if current_name:
                skills[current_name] = current
            current_name = stripped.rstrip(":").strip()
            current = {}
            continue
        if current_name and line.startswith("    "):
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key == "tags" and value.startswith("["):
                inner = value.strip("[]")
                current["tags"] = [t.strip().strip("'\"") for t in inner.split(",") if t.strip()]
            else:
                current[key] = value

    if current_name:
        skills[current_name] = current
    return skills


def load_community_mapping(path: Path | None = None) -> dict[str, dict[str, Any]]:
    community_path = path or DEFAULT_COMMUNITY_PATH
    if not community_path.is_file():
        return {}
    text = community_path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text) or {}
        skills = data.get("skills", {})
        return skills if isinstance(skills, dict) else {}
    except Exception:
        return _parse_simple_yaml_skills(text)


def community_document(name: str, meta: dict[str, Any]) -> str:
    tags = meta.get("tags", [])
    if isinstance(tags, list):
        tag_text = " ".join(str(t) for t in tags)
    else:
        tag_text = str(tags)
    return f"{name} {meta.get('description', '')} {tag_text}".strip()
