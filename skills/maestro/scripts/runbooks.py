#!/usr/bin/env python3
"""Load, validate and enrich Maestro runbooks without implicit execution."""

from __future__ import annotations

import json
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from maestro_paths import MAESTRO_HOME

BUNDLED_RUNBOOKS = Path(__file__).resolve().parent.parent / "skill-runbooks.json"
USER_RUNBOOKS = MAESTRO_HOME / "skill-runbooks.user.json"
PROJECT_RUNBOOKS_NAME = Path(".maestro") / "skill-runbooks.json"
DISCOVER_ALLOWLIST = MAESTRO_HOME / "discover-allowlist.txt"

ALLOWED_EFFECTS = {
    "read_local",
    "write_workspace",
    "network",
    "install_remote",
    "git_commit",
    "publish_external",
    "unknown",
}
MAX_RUNBOOK_BYTES = 1_000_000
MAX_PREFLIGHT_ARGS = 64
MAX_ARGUMENT_LENGTH = 4096


def _error(source: str, path: Path, message: str) -> dict[str, str]:
    return {"source": source, "path": str(path), "message": message}


def _read_json(path: Path, source: str) -> tuple[dict[str, Any], list[dict[str, str]]]:
    if not path.is_file():
        return {}, []
    try:
        if path.stat().st_size > MAX_RUNBOOK_BYTES:
            return {}, [_error(source, path, f"Runbook exceeds {MAX_RUNBOOK_BYTES} bytes.")]
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {}, [_error(source, path, f"Invalid JSON: {exc}")]
    if not isinstance(data, dict):
        return {}, [_error(source, path, "Top-level runbook value must be an object.")]
    return data, []


def _validate_preflight(
    value: Any,
    *,
    source: str,
    path: Path,
    skill_name: str,
    index: int,
) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    if not isinstance(value, dict):
        return None, [_error(source, path, f"skills.{skill_name}.preflight[{index}] must be an object.")]
    item = deepcopy(value)
    command = item.get("command")
    args = item.get("args", [])
    if not isinstance(command, str) or not command.strip():
        return None, [_error(source, path, f"skills.{skill_name}.preflight[{index}].command is required.")]
    if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
        return None, [_error(source, path, f"skills.{skill_name}.preflight[{index}].args must be strings.")]
    if len(args) > MAX_PREFLIGHT_ARGS or any(len(arg) > MAX_ARGUMENT_LENGTH for arg in args):
        return None, [_error(source, path, f"skills.{skill_name}.preflight[{index}].args exceeds safety limits.")]
    effect = str(item.get("effect", "read_local" if source == "bundled" else "unknown"))
    if effect not in ALLOWED_EFFECTS:
        return None, [_error(source, path, f"skills.{skill_name}.preflight[{index}].effect is invalid: {effect}")]
    required = bool(item.get("required", False))
    requires_confirmation = source != "bundled" or effect != "read_local"
    item.update(
        {
            "args": args,
            "effect": effect,
            "required": required,
            "provenance": source,
            "requires_confirmation": requires_confirmation,
            "enabled_by_default": required and not requires_confirmation,
        }
    )
    return item, []


def _validate_skill_map(
    data: dict[str, Any],
    *,
    source: str,
    path: Path,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    raw_skills = data.get("skills", {})
    if raw_skills is None:
        return {}, []
    if not isinstance(raw_skills, dict):
        return {}, [_error(source, path, "Field 'skills' must be an object.")]
    valid: dict[str, Any] = {}
    errors: list[dict[str, str]] = []
    for name, raw_entry in raw_skills.items():
        if str(name).startswith("_"):
            continue
        if not isinstance(raw_entry, dict):
            errors.append(_error(source, path, f"skills.{name} must be an object."))
            continue
        entry = deepcopy(raw_entry)
        entry["provenance"] = source
        raw_preflights = entry.get("preflight", [])
        if not isinstance(raw_preflights, list):
            errors.append(_error(source, path, f"skills.{name}.preflight must be a list."))
            entry["preflight"] = []
        else:
            preflights: list[dict[str, Any]] = []
            for index, raw_preflight in enumerate(raw_preflights):
                preflight, preflight_errors = _validate_preflight(
                    raw_preflight,
                    source=source,
                    path=path,
                    skill_name=str(name),
                    index=index,
                )
                errors.extend(preflight_errors)
                if preflight is not None:
                    preflights.append(preflight)
            entry["preflight"] = preflights
        valid[str(name)] = entry
    return valid, errors


def _merge_skill_maps(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for name, entry in override.items():
        if name not in merged:
            merged[name] = deepcopy(entry)
            continue
        current = merged[name]
        for key, value in entry.items():
            current[key] = deepcopy(value)
    return merged


def load_runbooks(project_root: Path | None = None) -> dict[str, Any]:
    project_path = project_root.resolve() / PROJECT_RUNBOOKS_NAME if project_root else None
    sources = [
        ("bundled", BUNDLED_RUNBOOKS),
        ("user", USER_RUNBOOKS),
    ]
    if project_path is not None:
        sources.append(("project", project_path))

    skills: dict[str, Any] = {}
    errors: list[dict[str, str]] = []
    present_sources: dict[str, str | None] = {"bundled": None, "user": None, "project": None}
    version = 1
    for source, path in sources:
        data, read_errors = _read_json(path, source)
        errors.extend(read_errors)
        if path.is_file():
            present_sources[source] = str(path)
        if source == "bundled" and isinstance(data.get("version"), int):
            version = data["version"]
        valid, validation_errors = _validate_skill_map(data, source=source, path=path)
        errors.extend(validation_errors)
        skills = _merge_skill_maps(skills, valid)

    return {
        "version": version,
        "skills": skills,
        "sources": present_sources,
        "errors": errors,
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
    replacements = {
        "{skill_root}": skill_root,
        "{skill_scripts}": str(scripts_dir),
        "{query}": query,
        "{project_name}": project_name,
    }
    resolved: list[str] = []
    for arg in preflight.get("args") or []:
        text = str(arg)
        for placeholder, value in replacements.items():
            text = text.replace(placeholder, value)
        resolved.append(text)
    return resolved


def _platform_command(preflight: dict[str, Any]) -> tuple[str, list[str]]:
    platforms = preflight.get("platforms")
    platform_key = "win32" if sys.platform == "win32" else "default"
    selected: dict[str, Any] = {}
    if isinstance(platforms, dict):
        candidate = platforms.get(platform_key) or platforms.get("default")
        if isinstance(candidate, dict):
            selected = candidate
    command = str(selected.get("command") or preflight.get("command") or "")
    prefix = selected.get("args_prefix") or []
    if not isinstance(prefix, list) or not all(isinstance(arg, str) for arg in prefix):
        prefix = []
    return command, list(prefix)


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
        if not isinstance(runbook, dict):
            continue
        rb = deepcopy(runbook)
        preflights = rb.get("preflight") or []
        if isinstance(preflights, list):
            for preflight in preflights:
                if not isinstance(preflight, dict):
                    continue
                skill_path = str(entry.get("path", ""))
                command, prefix = _platform_command(preflight)
                preflight["resolved_command"] = command
                preflight["resolved_args"] = [
                    *prefix,
                    *resolve_preflight_command(
                        preflight,
                        skill_path=skill_path,
                        query=query,
                        project_name=project_name,
                    ),
                ]
        entry["runbook"] = rb


def load_discover_allowlist() -> list[str]:
    if not DISCOVER_ALLOWLIST.is_file():
        return []
    return [
        line.strip().lower()
        for line in DISCOVER_ALLOWLIST.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _repo_identity(repo_ref: str) -> tuple[str, str | None] | None:
    value = repo_ref.strip().lower().rstrip("/")
    value = re.sub(r"^https?://github\.com/", "", value)
    value = re.sub(r"^github\.com/", "", value)
    value = value.removesuffix(".git")
    parts = value.split("/")
    if len(parts) != 2 or not all(parts):
        return None
    owner, repo_and_skill = parts
    repo, separator, skill = repo_and_skill.partition("@")
    if not re.fullmatch(r"[a-z0-9_.-]+", owner) or not re.fullmatch(r"[a-z0-9_.-]+", repo):
        return None
    if separator and not re.fullmatch(r"[a-z0-9_.-]+", skill):
        return None
    return f"{owner}/{repo}", skill or None


def is_repo_allowlisted(repo_ref: str, allowlist: list[str] | None = None) -> bool:
    candidate = _repo_identity(repo_ref)
    if candidate is None:
        return False
    entries = load_discover_allowlist() if allowlist is None else allowlist
    candidate_repo, candidate_skill = candidate
    for item in entries:
        allowed = _repo_identity(item)
        if allowed is None:
            continue
        allowed_repo, allowed_skill = allowed
        if allowed_repo != candidate_repo:
            continue
        if allowed_skill is None or allowed_skill == candidate_skill:
            return True
    return False
