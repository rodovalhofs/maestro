"""Tests for maestro hybrid skill routing."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "maestro" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from community import load_community_mapping  # noqa: E402
from intents import is_bypass_task, task_intents  # noqa: E402
from routing import build_routing, is_high_risk, select_mode  # noqa: E402
from route_tasks import route_batch  # noqa: E402
from search_skills import search_skills  # noqa: E402
from synonyms import expand_query  # noqa: E402

FIXTURE_MANIFEST = Path(__file__).parent / "fixtures" / "sample-manifest.json"
COMMUNITY = ROOT / "skills" / "maestro" / "community.yaml"


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


class TestSearchSkills(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = load_fixture()

    def test_superdesign_ranks_for_design_query(self) -> None:
        result = search_skills(
            "design landing page UI with superdesign",
            self.manifest,
            domain="design",
            community_path=COMMUNITY,
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
            community_path=COMMUNITY,
        )
        self.assertTrue(result["results"])
        self.assertEqual(
            result["results"][0]["name"],
            "performing-memory-forensics-with-volatility3",
        )

    def test_missing_skill_surfaced(self) -> None:
        result = search_skills(
            "search arxiv papers for related work",
            self.manifest,
            community_path=COMMUNITY,
        )
        missing_names = [m["skill"] for m in result.get("missing_skills", [])]
        self.assertIn("arxiv", missing_names)

    def test_ci_query_prefers_gh_fix_ci(self) -> None:
        result = search_skills(
            "corrigir CI quebrado no pull request",
            self.manifest,
            domain="devops-git",
            community_path=COMMUNITY,
        )
        self.assertEqual(result["results"][0]["name"], "gh-fix-ci")

    def test_bypass_routing(self) -> None:
        result = search_skills("oi", self.manifest, community_path=COMMUNITY)
        self.assertEqual(result["routing"]["priority"], "P3")
        self.assertEqual(result["routing"]["decision"], "bypass")


class TestRouteBatch(unittest.TestCase):
    def test_batch_returns_per_task_results(self) -> None:
        payload = route_batch(
            ["design dashboard ui", "fix failing CI on PR"],
            FIXTURE_MANIFEST,
            COMMUNITY,
        )
        self.assertTrue(payload["batch"])
        self.assertEqual(payload["task_count"], 2)
        self.assertEqual(len(payload["results"]), 2)
        self.assertIn("routing", payload)


class TestCommunity(unittest.TestCase):
    def test_community_yaml_loads(self) -> None:
        mapping = load_community_mapping(COMMUNITY)
        self.assertIn("superdesign", mapping)
        self.assertIn("install", mapping["superdesign"])


if __name__ == "__main__":
    unittest.main()
