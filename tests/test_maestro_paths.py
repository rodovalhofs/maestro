"""Tests for multi-agent skill roots."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "maestro" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from maestro_paths import GLOBAL_SKILL_ROOTS, project_skill_roots  # noqa: E402


class TestMaestroPaths(unittest.TestCase):
    def test_global_roots_include_codex(self) -> None:
        scopes = [scope for _, scope in GLOBAL_SKILL_ROOTS]
        self.assertIn("codex", scopes)
        codex_path = next(path for path, scope in GLOBAL_SKILL_ROOTS if scope == "codex")
        self.assertTrue(str(codex_path).replace("\\", "/").endswith("/.codex/skills"))

    def test_project_roots_include_codex(self) -> None:
        roots = project_skill_roots(Path("/tmp/project"))
        scopes = [scope for _, scope in roots]
        self.assertIn("project-codex", scopes)


if __name__ == "__main__":
    unittest.main()
