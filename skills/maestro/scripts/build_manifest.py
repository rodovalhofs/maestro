#!/usr/bin/env python3
"""Build skills-manifest.json for maestro from personal and project skills."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from domains import classify_skill  # noqa: E402

CURSOR_HOME = Path(os.environ.get("CURSOR_HOME", Path.home() / ".cursor"))
PERSONAL_SKILLS = CURSOR_HOME / "skills"
AGENTS_SKILLS = Path.home() / ".agents" / "skills"
MANIFEST_PATH = CURSOR_HOME / "skills-manifest.json"
EXCLUDE_PATH = CURSOR_HOME / "maestro-exclude.txt"
MAESTRO_NAMES = {"maestro"}


def parse_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    block = match.group(1)
    result: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_key, current_lines
        if current_key is not None:
            result[current_key] = "\n".join(current_lines).strip().strip('"').strip("'")
        current_key = None
        current_lines = []

    for line in block.splitlines():
        if re.match(r"^[A-Za-z0-9_-]+:\s*", line):
            flush()
            key, _, value = line.partition(":")
            current_key = key.strip()
            current_lines = [value.strip()]
        elif current_key is not None and (line.startswith("  ") or line.startswith("\t")):
            current_lines.append(line.strip())
        elif current_key is not None and line.strip():
            current_lines.append(line.strip())
    flush()
    return result


def parse_tags_from_text(text: str) -> list[str]:
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return []
    block = match.group(1)
    tags: list[str] = []
    in_tags = False
    for line in block.splitlines():
        stripped = line.strip()
        if re.match(r"^tags:\s*$", stripped):
            in_tags = True
            continue
        if re.match(r"^tags:\s*\[", stripped):
            inner = stripped.split("[", 1)[1].rstrip("]")
            tags.extend(
                item.strip().strip("'\"") for item in inner.split(",") if item.strip()
            )
            return tags
        if in_tags:
            if line.startswith("  - "):
                tags.append(line.strip()[2:].strip().strip('"').strip("'"))
            elif stripped and not line.startswith(" "):
                in_tags = False
    return tags


def load_exclude_list() -> set[str]:
    if not EXCLUDE_PATH.exists():
        return set()
    names: set[str] = set()
    for line in EXCLUDE_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        names.add(line.lower())
    return names


def iter_skill_dirs(root: Path, scope: str) -> list[dict]:
    if not root.is_dir():
        return []
    excluded = load_exclude_list()
    entries: list[dict] = []

    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        skill_md = child / "SKILL.md"
        if not skill_md.is_file():
            continue

        folder_name = child.name
        if folder_name.lower() in MAESTRO_NAMES or folder_name.lower() in excluded:
            continue

        text = skill_md.read_text(encoding="utf-8", errors="replace")
        meta = parse_frontmatter(text)
        name = meta.get("name", folder_name)
        description = meta.get("description", "")
        if not description:
            description = text[:400].replace("\n", " ")

        raw_domain = meta.get("domain", "")
        if raw_domain.lower() in {"cybersecurity", "security"}:
            skill_domain = "security"
        else:
            skill_domain = classify_skill(name, description)

        tags = parse_tags_from_text(text)

        entries.append(
            {
                "name": name,
                "folder": folder_name,
                "description": description[:1024],
                "tags": tags,
                "domain": skill_domain,
                "path": str(skill_md).replace("\\", "/"),
                "scope": scope,
                "installed": True,
            }
        )

    return entries


def build_manifest(project_root: Path | None) -> dict:
    skills: list[dict] = []
    skills.extend(iter_skill_dirs(PERSONAL_SKILLS, "personal"))
    skills.extend(iter_skill_dirs(AGENTS_SKILLS, "agents"))
    if project_root:
        project_skills = project_root / ".cursor" / "skills"
        skills.extend(iter_skill_dirs(project_skills, "project"))

    dedup: dict[str, dict] = {}
    for skill in skills:
        dedup[skill["folder"]] = skill

    return {
        "version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "personal_skills_root": str(PERSONAL_SKILLS).replace("\\", "/"),
        "agents_skills_root": str(AGENTS_SKILLS).replace("\\", "/"),
        "skill_count": len(dedup),
        "skills": sorted(dedup.values(), key=lambda s: (s["domain"], s["name"])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build maestro skills manifest")
    parser.add_argument("--project-root", default=None, help="Project root with .cursor/skills")
    parser.add_argument("--output", default=str(MANIFEST_PATH), help="Manifest output path")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve() if args.project_root else None
    manifest = build_manifest(project_root)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {manifest['skill_count']} skills to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
