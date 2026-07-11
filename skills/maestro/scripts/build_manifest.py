#!/usr/bin/env python3
"""Build the project-aware Maestro Skill Catalog manifest."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from catalog import (  # noqa: E402,F401
    CatalogError,
    build_catalog,
    parse_frontmatter,
    parse_tags_from_text,
    scan_skill_root,
)
from maestro_paths import MANIFEST_PATH  # noqa: E402


def configure_stdout_utf8() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass


def build_manifest(project_root: Path | None) -> dict:
    return build_catalog(project_root=project_root)


def write_manifest_atomic(output: Path, manifest: dict) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(manifest, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(output)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def main() -> int:
    configure_stdout_utf8()
    parser = argparse.ArgumentParser(description="Build maestro skills manifest")
    parser.add_argument("--project-root", default=None, help="Project root with agent skills dirs")
    parser.add_argument("--output", default=str(MANIFEST_PATH), help="Manifest output path")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve() if args.project_root else None
    output = Path(args.output)
    try:
        manifest = build_manifest(project_root)
        write_manifest_atomic(output, manifest)
    except (CatalogError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    print(f"Wrote {manifest['skill_count']} skills to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
