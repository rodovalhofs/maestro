"""Tests for skill runbook merge and discover allowlist."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "maestro" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from runbooks import (  # noqa: E402
    attach_runbooks,
    is_repo_allowlisted,
    load_discover_allowlist,
    load_runbooks,
    resolve_preflight_command,
)


class TestRunbooks(unittest.TestCase):
    def test_oversized_project_runbook_is_reported_and_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            runbook = project / ".maestro" / "skill-runbooks.json"
            runbook.parent.mkdir(parents=True)
            runbook.write_text(" " * 1_000_001, encoding="utf-8")

            data = load_runbooks(project)

            self.assertTrue(any("exceeds" in error["message"] for error in data["errors"]))
            self.assertNotIn("project-only", data["skills"])

    def test_bundled_has_ui_ux_pro_max(self) -> None:
        data = load_runbooks()
        skills = data["skills"]
        self.assertIn("ui-ux-pro-max", skills)
        self.assertTrue(skills["ui-ux-pro-max"].get("preflight"))

    def test_user_override_merge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            maestro_home = home / ".maestro"
            maestro_home.mkdir()
            user_file = maestro_home / "skill-runbooks.user.json"
            user_file.write_text(
                json.dumps(
                    {
                        "skills": {
                            "my-skill": {
                                "summary": "custom",
                                "preflight": [],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            # Patch MAESTRO_HOME for this test
            import runbooks as rb  # noqa: E402

            original = rb.MAESTRO_HOME
            rb.MAESTRO_HOME = maestro_home
            rb.USER_RUNBOOKS = maestro_home / "skill-runbooks.user.json"
            try:
                data = load_runbooks()
                self.assertIn("my-skill", data["skills"])
                self.assertIn("ui-ux-pro-max", data["skills"])
            finally:
                rb.MAESTRO_HOME = original
                rb.USER_RUNBOOKS = original / "skill-runbooks.user.json"

    def test_attach_runbooks_resolves_placeholders(self) -> None:
        results = [
            {
                "name": "ui-ux-pro-max",
                "folder": "ui-ux-pro-max",
                "path": "/tmp/skills/ui-ux-pro-max/SKILL.md",
            }
        ]
        runbooks = load_runbooks()
        attach_runbooks(results, runbooks, query="dashboard", project_name="Demo")
        rb = results[0]["runbook"]
        pf = rb["preflight"][0]
        self.assertIn("resolved_args", pf)
        self.assertIn("dashboard", pf["resolved_args"])

    def test_resolve_preflight_command(self) -> None:
        args = resolve_preflight_command(
            {
                "args": ["{skill_scripts}/search.py", "{query}", "-p", "{project_name}"],
            },
            skill_path="/skills/foo/SKILL.md",
            query="landing page",
            project_name="Acme",
        )
        self.assertTrue(str(args[0]).endswith("search.py"))
        self.assertEqual(args[1], "landing page")
        self.assertEqual(args[3], "Acme")

    def test_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            import runbooks as rb  # noqa: E402

            path = Path(tmp) / "discover-allowlist.txt"
            path.write_text("# comment\nrodovalhofs/maestro\n", encoding="utf-8")
            original = rb.DISCOVER_ALLOWLIST
            rb.DISCOVER_ALLOWLIST = path
            try:
                items = load_discover_allowlist()
                self.assertEqual(items, ["rodovalhofs/maestro"])
                self.assertTrue(is_repo_allowlisted("rodovalhofs/maestro"))
                self.assertFalse(is_repo_allowlisted("evil/unknown"))
                self.assertFalse(
                    is_repo_allowlisted("attacker/rodovalhofs/maestro-malware")
                )
            finally:
                rb.DISCOVER_ALLOWLIST = original

    def test_invalid_project_entry_is_reported_and_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            config_dir = project / ".maestro"
            config_dir.mkdir()
            (config_dir / "skill-runbooks.json").write_text(
                json.dumps({"skills": {"tdd": "not-an-object"}}),
                encoding="utf-8",
            )

            data = load_runbooks(project)

            self.assertNotIn("tdd", data["skills"])
            self.assertTrue(data["errors"])
            self.assertIn("tdd", data["errors"][0]["message"])

    def test_malformed_project_json_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            config_dir = project / ".maestro"
            config_dir.mkdir()
            (config_dir / "skill-runbooks.json").write_text("{broken", encoding="utf-8")

            data = load_runbooks(project)

            self.assertTrue(data["errors"])
            self.assertEqual(data["errors"][0]["source"], "project")

    def test_project_preflight_requires_confirmation_and_has_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            config_dir = project / ".maestro"
            config_dir.mkdir()
            (config_dir / "skill-runbooks.json").write_text(
                json.dumps(
                    {
                        "skills": {
                            "custom": {
                                "summary": "custom",
                                "preflight": [
                                    {
                                        "id": "probe",
                                        "command": "python",
                                        "args": ["--version"],
                                        "effect": "read_local",
                                        "required": True,
                                    }
                                ],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            results = [
                {
                    "name": "custom",
                    "folder": "custom",
                    "path": "/skills/custom/SKILL.md",
                }
            ]

            runbooks = load_runbooks(project)
            attach_runbooks(results, runbooks, query="inspect", project_name="Demo")

            preflight = results[0]["runbook"]["preflight"][0]
            self.assertEqual(preflight["provenance"], "project")
            self.assertTrue(preflight["requires_confirmation"])
            self.assertEqual(preflight["effect"], "read_local")

    def test_optional_write_preflight_is_not_enabled_by_default(self) -> None:
        results = [
            {
                "name": "ui-ux-pro-max",
                "folder": "ui-ux-pro-max",
                "path": "/tmp/skills/ui-ux-pro-max/SKILL.md",
            }
        ]
        runbooks = load_runbooks()
        attach_runbooks(results, runbooks, query="dashboard", project_name="Demo")

        persist = next(
            item
            for item in results[0]["runbook"]["preflight"]
            if item["id"] == "design-system-persist"
        )
        self.assertFalse(persist["required"])
        self.assertEqual(persist["effect"], "write_workspace")
        self.assertFalse(persist["enabled_by_default"])


if __name__ == "__main__":
    unittest.main()
