"""Behavior tests for the project-aware Skill Catalog interface."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "maestro" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from catalog import (  # noqa: E402
    CatalogError,
    build_catalog,
    catalog_for_project,
)


def write_skill(root: Path, folder: str, name: str, description: str) -> Path:
    skill_dir = root / folder
    skill_dir.mkdir(parents=True, exist_ok=True)
    path = skill_dir / "SKILL.md"
    path.write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n",
        encoding="utf-8",
    )
    return path


class TestSkillCatalog(unittest.TestCase):
    def test_body_content_is_not_copied_when_description_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills"
            skill_dir = root / "private-helper"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: private-helper\n---\nAPI_TOKEN=do-not-index-this\n",
                encoding="utf-8",
            )

            manifest = build_catalog(
                global_roots=[(root, "codex")],
                plugin_root=None,
            )

            self.assertNotIn("do-not-index-this", manifest["skills"][0]["description"])

    def test_current_project_replaces_foreign_project_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            global_root = base / "global"
            project_a = base / "project-a"
            project_b = base / "project-b"
            write_skill(global_root, "shared", "shared", "Shared workflow")
            write_skill(project_a / ".codex" / "skills", "only-a", "only-a", "A workflow")
            write_skill(project_b / ".codex" / "skills", "only-b", "only-b", "B workflow")

            manifest = build_catalog(
                global_roots=[(global_root, "codex")],
                project_root=project_a,
                plugin_root=None,
            )
            skills = catalog_for_project(manifest, project_b)
            names = {skill["name"] for skill in skills}

            self.assertEqual(names, {"shared", "only-b"})
            self.assertNotIn("only-a", names)

    def test_duplicate_skill_has_one_selected_path_and_all_locations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            universal = base / "agents"
            codex = base / "codex"
            universal_path = write_skill(universal, "review", "review", "Universal review")
            codex_path = write_skill(codex, "review", "review", "Codex review")

            manifest = build_catalog(
                global_roots=[(universal, "agents"), (codex, "codex")],
                plugin_root=None,
            )

            self.assertEqual(manifest["skill_count"], 1)
            skill = manifest["skills"][0]
            self.assertEqual(Path(skill["path"]), codex_path)
            self.assertEqual(
                {Path(location["path"]) for location in skill["locations"]},
                {universal_path, codex_path},
            )

    def test_codex_plugin_skills_are_namespaced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            plugin_root = base / "cache"
            skill_root = (
                plugin_root
                / "openai-curated-remote"
                / "github"
                / "1.2.3"
                / "skills"
            )
            skill_path = write_skill(
                skill_root,
                "gh-fix-ci",
                "gh-fix-ci",
                "Fix failing GitHub Actions checks",
            )

            manifest = build_catalog(global_roots=[], plugin_root=plugin_root)

            self.assertEqual(manifest["skill_count"], 1)
            skill = manifest["skills"][0]
            self.assertEqual(skill["name"], "github:gh-fix-ci")
            self.assertEqual(Path(skill["path"]), skill_path)
            self.assertEqual(skill["plugin"], "github")

    def test_codex_plugin_selects_latest_numeric_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin_root = Path(tmp) / "cache"
            older = plugin_root / "publisher" / "github" / "9.9.0" / "skills"
            newer = plugin_root / "publisher" / "github" / "10.0.0" / "skills"
            write_skill(older, "review", "review", "Old review")
            newest = write_skill(newer, "review", "review", "New review")

            manifest = build_catalog(global_roots=[], plugin_root=plugin_root)

            self.assertEqual(Path(manifest["skills"][0]["path"]), newest)
            self.assertEqual(manifest["skills"][0]["plugin_version"], "10.0.0")

    def test_invalid_manifest_version_is_rejected(self) -> None:
        with self.assertRaises(CatalogError):
            catalog_for_project({"version": 999, "skills": []}, Path.cwd())

    def test_invalid_manifest_skill_entry_is_rejected(self) -> None:
        with self.assertRaisesRegex(CatalogError, r"skills\[0\] must be an object"):
            catalog_for_project({"version": 4, "skills": [None]}, Path.cwd())


if __name__ == "__main__":
    unittest.main()
