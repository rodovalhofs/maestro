#!/usr/bin/env python3
"""Project-aware Skill Catalog with provenance and host providers."""

from __future__ import annotations

import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from domains import DOMAINS, classify_skill
from maestro_paths import (
    CODEX_PLUGIN_CACHE,
    EXCLUDE_PATH,
    GLOBAL_SKILL_ROOTS,
    MANIFEST_PATH,
    project_skill_roots,
)

CATALOG_VERSION = 4
MAX_SKILL_METADATA_BYTES = 65_536
SUPPORTED_MANIFEST_VERSIONS = {2, 3, CATALOG_VERSION}
MAESTRO_NAMES = {"maestro"}

SCOPE_PRIORITY = {
    "agents": 50,
    "codex-plugin": 60,
    "cursor": 70,
    "claude": 70,
    "codex-system": 75,
    "codex": 80,
}


class CatalogError(ValueError):
    """Raised when a manifest cannot safely be used."""


def _path_text(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse the small YAML subset used by SKILL.md without a dependency."""
    match = re.match(r"^---\s*\r?\n(.*?)\r?\n---", text, re.DOTALL)
    if not match:
        return {}

    lines = match.group(1).splitlines()
    result: dict[str, str] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        key_match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not key_match:
            index += 1
            continue
        key, raw_value = key_match.groups()
        raw_value = raw_value.strip()
        if raw_value in {">", ">-", "|", "|-"}:
            folded = raw_value.startswith(">")
            block: list[str] = []
            index += 1
            while index < len(lines) and (
                lines[index].startswith(" ") or not lines[index].strip()
            ):
                block.append(lines[index].strip())
                index += 1
            value = " ".join(part for part in block if part) if folded else "\n".join(block)
            result[key] = value.strip()
            continue
        result[key] = raw_value.strip().strip('"').strip("'")
        index += 1
    return result


def parse_tags_from_text(text: str) -> list[str]:
    match = re.match(r"^---\s*\r?\n(.*?)\r?\n---", text, re.DOTALL)
    if not match:
        return []
    block = match.group(1)
    inline = re.search(r"^tags:\s*\[(.*?)\]\s*$", block, re.MULTILINE)
    if inline:
        return [
            item.strip().strip("'\"")
            for item in inline.group(1).split(",")
            if item.strip()
        ]
    listed = re.search(r"^tags:\s*$((?:\r?\n\s+-\s+.*)+)", block, re.MULTILINE)
    if not listed:
        return []
    return [
        line.split("-", 1)[1].strip().strip("'\"")
        for line in listed.group(1).splitlines()
        if "-" in line
    ]


def load_exclude_list(path: Path = EXCLUDE_PATH) -> set[str]:
    if not path.is_file():
        return set()
    return {
        line.strip().casefold()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def resolve_skill_domain(name: str, description: str, raw_domain: str) -> str:
    """Prefer a valid declared domain and infer only when it is absent or invalid."""
    declared = raw_domain.strip().lower()
    if declared == "cybersecurity":
        declared = "security"
    if declared in DOMAINS:
        return declared
    return classify_skill(name, description)


def _read_skill(
    skill_md: Path,
    *,
    scope: str,
    source_root: Path,
    namespace: str | None = None,
    plugin: str | None = None,
    plugin_version: str | None = None,
) -> dict[str, Any]:
    with skill_md.open("r", encoding="utf-8", errors="replace") as handle:
        text = handle.read(MAX_SKILL_METADATA_BYTES)
    meta = parse_frontmatter(text)
    raw_name = meta.get("name", skill_md.parent.name)
    name = f"{namespace}:{raw_name}" if namespace else raw_name
    # Catalog only declared metadata. Never copy arbitrary skill body content into
    # a shared manifest when a description is absent.
    description = meta.get("description", "") or f"Installed skill: {raw_name}"
    tags = parse_tags_from_text(text)
    raw_domain = meta.get("domain", "").strip().lower()
    domain = resolve_skill_domain(raw_name, f"{description} {' '.join(tags)}", raw_domain)
    entry: dict[str, Any] = {
        "name": name,
        "folder": skill_md.parent.name,
        "description": description[:1024],
        "tags": tags,
        "domain": domain,
        "path": _path_text(skill_md),
        "source_root": _path_text(source_root),
        "scope": scope,
        "installed": True,
    }
    if plugin:
        entry["plugin"] = plugin
    if plugin_version:
        entry["plugin_version"] = plugin_version
    return entry


def scan_skill_root(
    root: Path,
    scope: str,
    *,
    excluded: set[str] | None = None,
) -> list[dict[str, Any]]:
    if not root.is_dir():
        return []
    excluded = load_exclude_list() if excluded is None else excluded
    entries: list[dict[str, Any]] = []
    for child in sorted(root.iterdir(), key=lambda path: path.name.casefold()):
        if not child.is_dir():
            continue
        skill_md = child / "SKILL.md"
        if not skill_md.is_file():
            continue
        if child.name.casefold() in MAESTRO_NAMES or child.name.casefold() in excluded:
            continue
        entries.append(_read_skill(skill_md, scope=scope, source_root=root))
    return entries


def scan_codex_plugins(
    plugin_root: Path | None = CODEX_PLUGIN_CACHE,
    *,
    excluded: set[str] | None = None,
) -> list[dict[str, Any]]:
    if plugin_root is None or not plugin_root.is_dir():
        return []
    excluded = load_exclude_list() if excluded is None else excluded
    selected: dict[tuple[str, str, str], tuple[str, Path]] = {}
    for skill_md in plugin_root.glob("*/*/*/skills/*/SKILL.md"):
        relative = skill_md.relative_to(plugin_root)
        if len(relative.parts) != 6:
            continue
        publisher, plugin, version, marker, folder, _ = relative.parts
        if marker != "skills" or folder.casefold() in excluded:
            continue
        key = (publisher.casefold(), plugin.casefold(), folder.casefold())
        current = selected.get(key)
        if current is None or _version_key(version) > _version_key(current[0]):
            selected[key] = (version, skill_md)

    entries: list[dict[str, Any]] = []
    for (_, plugin, _), (version, skill_md) in sorted(selected.items()):
        entries.append(
            _read_skill(
                skill_md,
                scope="codex-plugin",
                source_root=plugin_root,
                namespace=plugin,
                plugin=plugin,
                plugin_version=version,
            )
        )
    return entries


def _version_key(version: str) -> tuple[tuple[int, int | str], ...]:
    """Compare numeric version segments numerically with a stable text fallback."""
    parts = re.split(r"[.+-]", version.casefold())
    return tuple((1, int(part)) if part.isdigit() else (0, part) for part in parts)


def _priority(skill: dict[str, Any]) -> int:
    scope = str(skill.get("scope", ""))
    if scope.startswith("project-"):
        return 100
    return SCOPE_PRIORITY.get(scope, 40)


def deduplicate_skills(skills: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for skill in skills:
        name = str(skill.get("name", "")).strip()
        path = str(skill.get("path", "")).strip()
        if not name or not path:
            continue
        groups.setdefault(name.casefold(), []).append(deepcopy(skill))

    result: list[dict[str, Any]] = []
    for group in groups.values():
        ordered = sorted(
            group,
            key=lambda skill: (_priority(skill), str(skill.get("path", ""))),
            reverse=True,
        )
        selected = ordered[0]
        locations: list[dict[str, str]] = []
        seen_paths: set[str] = set()
        for entry in ordered:
            path = str(entry["path"])
            if path.casefold() in seen_paths:
                continue
            seen_paths.add(path.casefold())
            locations.append(
                {
                    "path": path,
                    "scope": str(entry.get("scope", "")),
                    "source_root": str(entry.get("source_root", "")),
                }
            )
        selected["locations"] = locations
        result.append(selected)
    return sorted(result, key=lambda skill: (str(skill.get("domain", "")), str(skill["name"]).casefold()))


def _scan_roots(
    roots: Iterable[tuple[Path, str]],
    *,
    excluded: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    entries: list[dict[str, Any]] = []
    scanned: list[dict[str, str]] = []
    for root, scope in roots:
        scanned.append({"path": _path_text(root), "scope": scope})
        entries.extend(scan_skill_root(root, scope, excluded=excluded))
    return entries, scanned


def build_catalog(
    project_root: Path | None = None,
    *,
    global_roots: Iterable[tuple[Path, str]] | None = None,
    plugin_root: Path | None = CODEX_PLUGIN_CACHE,
) -> dict[str, Any]:
    excluded = load_exclude_list()
    roots = list(GLOBAL_SKILL_ROOTS if global_roots is None else global_roots)
    entries, scanned = _scan_roots(roots, excluded=excluded)
    if plugin_root is not None:
        scanned.append({"path": _path_text(plugin_root), "scope": "codex-plugin"})
        entries.extend(scan_codex_plugins(plugin_root, excluded=excluded))
    if project_root is not None:
        project_entries, project_scanned = _scan_roots(
            project_skill_roots(project_root), excluded=excluded
        )
        entries.extend(project_entries)
        scanned.extend(project_scanned)
    skills = deduplicate_skills(entries)
    return {
        "version": CATALOG_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "maestro_home": _path_text(MANIFEST_PATH.parent),
        "project_root": _path_text(project_root) if project_root else None,
        "scanned_roots": scanned,
        "skill_count": len(skills),
        "skills": skills,
    }


def validate_manifest(manifest: dict[str, Any]) -> None:
    if not isinstance(manifest, dict):
        raise CatalogError("Manifest must be a JSON object.")
    version = manifest.get("version")
    if version not in SUPPORTED_MANIFEST_VERSIONS:
        raise CatalogError(
            f"Unsupported manifest version {version!r}; rebuild with: maestro-skills manifest"
        )
    if not isinstance(manifest.get("skills"), list):
        raise CatalogError("Manifest field 'skills' must be a list.")
    for index, skill in enumerate(manifest["skills"]):
        if not isinstance(skill, dict):
            raise CatalogError(f"Manifest skills[{index}] must be an object.")
        for field in ("name", "path"):
            if not isinstance(skill.get(field), str) or not skill[field].strip():
                raise CatalogError(
                    f"Manifest skills[{index}].{field} must be a non-empty string."
                )


def catalog_for_project(manifest: dict[str, Any], project_root: Path | None) -> list[dict[str, Any]]:
    """Return global skills plus a fresh overlay for only the current project."""
    validate_manifest(manifest)
    global_skills = [
        deepcopy(skill)
        for skill in manifest["skills"]
        if not str(skill.get("scope", "")).startswith("project-")
    ]
    if project_root is None:
        return deduplicate_skills(global_skills)
    excluded = load_exclude_list()
    project_entries, _ = _scan_roots(project_skill_roots(project_root), excluded=excluded)
    return deduplicate_skills([*global_skills, *project_entries])
