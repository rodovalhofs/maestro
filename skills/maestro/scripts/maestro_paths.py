#!/usr/bin/env python3
"""Shared paths for Maestro (multi-agent, agent-agnostic home)."""

from __future__ import annotations

import os
from pathlib import Path

MAESTRO_HOME = Path(os.environ.get("MAESTRO_HOME", Path.home() / ".maestro"))
MANIFEST_PATH = MAESTRO_HOME / "skills-manifest.json"
EXCLUDE_PATH = MAESTRO_HOME / "maestro-exclude.txt"
CONFIG_PATH = MAESTRO_HOME / "config.json"

LEGACY_CURSOR_HOME = Path(os.environ.get("CURSOR_HOME", Path.home() / ".cursor"))
LEGACY_MANIFEST_PATH = LEGACY_CURSOR_HOME / "skills-manifest.json"
LEGACY_EXCLUDE_PATH = LEGACY_CURSOR_HOME / "maestro-exclude.txt"

# (skills directory, scope label)
GLOBAL_SKILL_ROOTS: list[tuple[Path, str]] = [
    (Path.home() / ".cursor" / "skills", "cursor"),
    (Path.home() / ".claude" / "skills", "claude"),
    (Path.home() / ".codex" / "skills", "codex"),
    (Path.home() / ".agents" / "skills", "agents"),
]


def project_skill_roots(project_root: Path) -> list[tuple[Path, str]]:
    root = project_root.resolve()
    return [
        (root / ".cursor" / "skills", "project-cursor"),
        (root / ".claude" / "skills", "project-claude"),
        (root / ".codex" / "skills", "project-codex"),
        (root / ".agents" / "skills", "project-agents"),
    ]


def all_skill_roots(project_root: Path | None = None) -> list[tuple[Path, str]]:
    roots = list(GLOBAL_SKILL_ROOTS)
    if project_root:
        roots.extend(project_skill_roots(project_root))
    return roots
