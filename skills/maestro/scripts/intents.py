#!/usr/bin/env python3
"""Workflow intent profiles that boost BM25 matches beyond raw text similarity."""

from __future__ import annotations

import re
from typing import Any

INTENT_PROFILES: list[dict[str, Any]] = [
    {
        "name": "root-cause-debugging",
        "task_patterns": [
            r"\b(root[- ]?cause|debug|bug|bugs?|crash|exception|traceback)\b",
            r"\b(failing tests?|test failures?)\b",
            r"\b(depurar|depuracao|raiz|falhando|erro|bug)\b",
        ],
        "skill_patterns": [
            r"systematic-debugging",
            r"root[- ]?cause",
            r"troubleshooting",
            r"problem-solving",
        ],
        "score_multiplier": 1.45,
        "min_boost": 1.5,
        "suggested_mode": "auto-load",
    },
    {
        "name": "frontend-design",
        "task_patterns": [
            r"\b(landing page|redesign|ui|frontend|visual design|superdesign)\b",
            r"\b(dashboard|mockup|wireframe|figma)\b",
            r"\b(interface|layout|design system)\b",
        ],
        "skill_patterns": [
            r"superdesign",
            r"shadcn",
            r"frontend",
            r"ui-ux",
            r"design",
            r"mockup",
        ],
        "score_multiplier": 1.4,
        "min_boost": 1.2,
        "suggested_mode": "auto-load",
    },
    {
        "name": "devops-ci",
        "task_patterns": [
            r"\b(ci|github actions|pull request|pr|pipeline)\b",
            r"\b(falhando|quebrado|fix ci)\b",
        ],
        "skill_patterns": [
            r"gh-fix-ci",
            r"github",
            r"yeet",
            r"ci",
        ],
        "score_multiplier": 1.35,
        "min_boost": 1.0,
        "suggested_mode": "auto-load",
    },
    {
        "name": "security-forensics",
        "task_patterns": [
            r"\b(forensics|volatility|memory dump|credential|mitre|dfir)\b",
            r"\b(seguranca|forense|malware|incident)\b",
        ],
        "skill_patterns": [
            r"forensics",
            r"volatility",
            r"credential",
            r"malware",
            r"incident-response",
        ],
        "score_multiplier": 1.5,
        "min_boost": 2.0,
        "suggested_mode": "auto-load",
    },
    {
        "name": "skill-discovery",
        "task_patterns": [
            r"\bfind (a )?skill\b",
            r"\bnpx skills\b",
            r"\bskills\.sh\b",
            r"\btem skill (para|de)\b",
            r"\binstalar skill\b",
            r"\bis there a skill\b",
            r"\bdiscover (agent )?skills\b",
        ],
        "skill_patterns": [
            r"find-skills",
            r"create-skill",
            r"skill-creator",
            r"skill-installer",
        ],
        "score_multiplier": 2.0,
        "min_boost": 3.0,
        "suggested_mode": "auto-load",
    },
]

FORCE_DISCOVER_PATTERNS: list[str] = [
    r"\bfind (a )?skill\b",
    r"\bnpx skills\b",
    r"\bskills\.sh\b",
    r"\btem skill (para|de)\b",
    r"\binstalar skill\b",
    r"\bis there a skill\b",
    r"\bdiscover (agent )?skills\b",
]

BYPASS_PATTERNS = [
    r"^\s*(hi|hello|hey|oi|ola|olá)\b",
    r"^\s*(what time|que horas)\b",
]


def matches_any_pattern(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def is_bypass_task(task: str) -> bool:
    task_lower = task.strip().lower()
    if not task_lower:
        return False
    return matches_any_pattern(task_lower, BYPASS_PATTERNS)


def is_force_discover(task: str) -> bool:
    if is_bypass_task(task):
        return False
    return matches_any_pattern(task, FORCE_DISCOVER_PATTERNS)


def task_intents(task: str) -> list[dict[str, Any]]:
    if is_bypass_task(task):
        return []
    return [
        profile
        for profile in INTENT_PROFILES
        if matches_any_pattern(task, list(profile.get("task_patterns", [])))
    ]


def apply_intent_boost(
    score: float,
    skill_name: str,
    skill_text: str,
    intents: list[dict[str, Any]],
) -> tuple[float, list[str], str]:
    adjusted = score
    matched: list[str] = []
    suggested_mode = ""
    searchable = f"{skill_name} {skill_text}".lower()

    for profile in intents:
        if not matches_any_pattern(searchable, list(profile.get("skill_patterns", []))):
            continue
        matched.append(str(profile.get("name", "")))
        multiplier = float(profile.get("score_multiplier", 1.0))
        min_boost = float(profile.get("min_boost", 0.0))
        adjusted = max(adjusted * multiplier, min_boost)
        mode = str(profile.get("suggested_mode", "") or "")
        if mode:
            suggested_mode = mode

    return adjusted, [name for name in matched if name], suggested_mode
