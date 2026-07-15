"""Tests for maestro hybrid skill routing."""

from __future__ import annotations

from copy import deepcopy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "maestro" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from concept_gaps import extract_concept_candidates, find_concept_gaps  # noqa: E402
from domains import classify_query  # noqa: E402
from intents import is_bypass_task, is_force_discover, task_intents  # noqa: E402
from routing import build_routing, is_high_risk, select_mode  # noqa: E402
from route_tasks import route_batch  # noqa: E402
from search_skills import search_skills, skill_document  # noqa: E402
from synonyms import expand_query  # noqa: E402

FIXTURE_MANIFEST = Path(__file__).parent / "fixtures" / "sample-manifest.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE_MANIFEST.read_text(encoding="utf-8"))


class TestSynonyms(unittest.TestCase):
    def test_portuguese_debug_expansion(self) -> None:
        expanded = expand_query("depurar teste falhando")
        self.assertIn("debug", expanded)
        self.assertIn("test", expanded)


class TestIntents(unittest.TestCase):
    def test_debug_intent_detected(self) -> None:
        intents = task_intents("inspect failing test and find root cause")
        names = [i["name"] for i in intents]
        self.assertIn("root-cause-debugging", names)

    def test_bypass_greeting(self) -> None:
        self.assertTrue(is_bypass_task("oi"))

    def test_force_discover_intent(self) -> None:
        self.assertTrue(is_force_discover("find a skill for changelog"))
        self.assertTrue(is_force_discover("tem skill para deploy"))
        self.assertFalse(is_force_discover("corrigir CI no PR"))

    def test_skill_discovery_intent_profile(self) -> None:
        intents = task_intents("npx skills find react")
        names = [i["name"] for i in intents]
        self.assertIn("skill-discovery", names)


class TestDomains(unittest.TestCase):
    def test_safe_execution_phrase_is_not_cybersecurity(self) -> None:
        for query in (
            "refatorar codigo legado com seguranca",
            "refatorar código legado com segurança",
        ):
            domain, scores = classify_query(query)
            self.assertEqual(domain, "general")
            self.assertEqual(scores["security"], 0)

    def test_explicit_security_context_remains_security(self) -> None:
        domain, scores = classify_query(
            "revisar segurança da aplicação e vulnerabilidades"
        )
        self.assertEqual(domain, "security")
        self.assertGreater(scores["security"], 0)


class TestRouting(unittest.TestCase):
    def test_high_risk_forces_recommend(self) -> None:
        self.assertTrue(is_high_risk("deploy to production with token"))
        mode = select_mode(0.9, high_risk=True)
        self.assertEqual(mode, "recommend")

    def test_p1_auto_load(self) -> None:
        matches = [{"confidence": 0.4, "mode": "auto-load"}]
        routing = build_routing("design dashboard ui", matches, high_risk=False)
        self.assertEqual(routing["priority"], "P1")
        self.assertEqual(routing["decision"], "auto-load")


class TestConceptGaps(unittest.TestCase):
    def test_extract_skeleton_loader(self) -> None:
        query = "vamos fazer uma alteração na ui e vamos colocar skeleton-loader"
        candidates = extract_concept_candidates(query)
        self.assertIn("skeleton-loader", candidates)

    def test_ui_is_stopword(self) -> None:
        query = "melhorar a ui do app"
        candidates = extract_concept_candidates(query)
        self.assertNotIn("ui", candidates)


class TestSearchSkills(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = load_fixture()

    def test_superdesign_ranks_for_design_query(self) -> None:
        result = search_skills(
            "design landing page UI with superdesign",
            self.manifest,
            domain="design",
        )
        self.assertTrue(result["results"])
        self.assertEqual(result["results"][0]["name"], "superdesign")
        self.assertIn("routing", result)
        self.assertIn(result["routing"]["priority"], {"P1", "P2"})

    def test_forensics_intent_boost(self) -> None:
        result = search_skills(
            "memory forensics credential dumping volatility",
            self.manifest,
            domain="security",
        )
        self.assertTrue(result["results"])
        self.assertEqual(
            result["results"][0]["name"],
            "performing-memory-forensics-with-volatility3",
        )

    def test_concept_gap_triggers_discover(self) -> None:
        result = search_skills(
            "vamos fazer uma alteração na ui e vamos colocar skeleton-loader",
            self.manifest,
            domain="web",
        )
        discover = result["discover"]
        self.assertTrue(discover["triggered"])
        self.assertIn("concept_gap", discover["reasons"])
        self.assertIn("skeleton-loader", discover["gaps"])
        self.assertTrue(discover["queries"])
        self.assertFalse(result.get("missing_skills"))

    def test_force_discover_triggers_even_with_strong_local(self) -> None:
        result = search_skills(
            "find a skill for react performance",
            self.manifest,
            domain="web",
        )
        discover = result["discover"]
        self.assertTrue(discover["triggered"])
        self.assertTrue(discover["force_discover"])
        self.assertIn("force_discover", discover["reasons"])

    def test_ci_query_no_discover(self) -> None:
        result = search_skills(
            "corrigir CI quebrado no pull request",
            self.manifest,
            domain="devops-git",
        )
        self.assertEqual(result["results"][0]["name"], "gh-fix-ci")
        self.assertFalse(result["discover"]["triggered"])

    def test_safe_refactoring_outranks_security_for_safe_execution_phrase(self) -> None:
        manifest = deepcopy(self.manifest)
        manifest["skills"].extend(
            [
                {
                    "name": "safe-refactoring",
                    "folder": "safe-refactoring",
                    "description": (
                        "Refactor and restructure legacy code without changing "
                        "observable behavior using regression tests"
                    ),
                    "tags": ["refactoring", "refatoracao", "legacy-code", "codigo-legado"],
                    "domain": "general",
                    "path": "/tmp/skills/safe-refactoring/SKILL.md",
                    "scope": "project-agents",
                    "installed": True,
                },
                {
                    "name": "ransomware-security-analysis",
                    "folder": "ransomware-security-analysis",
                    "description": "Analyze ransomware and security incidents",
                    "tags": ["ransomware", "seguranca", "malware"],
                    "domain": "security",
                    "path": "/tmp/skills/ransomware-security-analysis/SKILL.md",
                    "scope": "agents",
                    "installed": True,
                },
            ]
        )

        result = search_skills(
            "refatorar codigo legado com seguranca",
            manifest,
        )

        self.assertEqual(result["domain"], "general")
        self.assertEqual(result["results"][0]["name"], "safe-refactoring")

    def test_bypass_routing(self) -> None:
        result = search_skills("oi", self.manifest)
        self.assertEqual(result["routing"]["priority"], "P3")
        self.assertEqual(result["routing"]["decision"], "bypass")
        self.assertFalse(result["discover"]["triggered"])


class TestRouteBatch(unittest.TestCase):
    def test_batch_returns_per_task_results(self) -> None:
        payload = route_batch(
            ["design dashboard ui", "fix failing CI on PR"],
            FIXTURE_MANIFEST,
        )
        self.assertTrue(payload["batch"])
        self.assertEqual(payload["task_count"], 2)
        self.assertEqual(len(payload["results"]), 2)
        self.assertIn("routing", payload)
        self.assertIn("discover", payload)

    def test_cli_accepts_domain(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "route_tasks.py"),
                "--manifest",
                str(FIXTURE_MANIFEST),
                "--domain",
                "general",
                "--json",
            ],
            input="modelar dominio\n",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["task_count"], 1)
        self.assertEqual(payload["results"][0]["domain"], "general")


if __name__ == "__main__":
    unittest.main()
