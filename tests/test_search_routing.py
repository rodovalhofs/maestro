"""Tests for maestro hybrid skill routing."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "maestro" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from concept_gaps import extract_concept_candidates, find_concept_gaps  # noqa: E402
from domains import classify_query, classify_skill  # noqa: E402
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

    def test_short_synonyms_match_words_not_substrings(self) -> None:
        self.assertNotIn("github", expand_query("melhorar a vida do programador"))
        self.assertIn("github", expand_query("revisar o PR"))


class TestDomains(unittest.TestCase):
    def test_short_keywords_match_words_not_substrings(self) -> None:
        self.assertEqual(classify_query("funciona")[0], "general")
        self.assertNotEqual(classify_skill("tdd", "Build features and tests"), "design")

    def test_dependency_graph_is_not_data_visualization(self) -> None:
        domain, _ = classify_query("map the dependency graph in this repository")
        self.assertNotEqual(domain, "data-viz")


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


class TestRouting(unittest.TestCase):
    def test_high_risk_terms_use_word_boundaries(self) -> None:
        self.assertFalse(is_high_risk("review the author profile"))
        self.assertFalse(is_high_risk("explain tokenization"))
        self.assertTrue(is_high_risk("rotate the auth token"))
        self.assertTrue(is_high_risk("deploy em produção"))

    def test_high_risk_forces_recommend(self) -> None:
        self.assertTrue(is_high_risk("deploy to production with token"))
        mode = select_mode(0.9, high_risk=True)
        self.assertEqual(mode, "recommend")

    def test_p1_auto_load(self) -> None:
        matches = [{"confidence": 0.4, "mode": "auto-load"}]
        routing = build_routing("design dashboard ui", matches, high_risk=False)
        self.assertEqual(routing["priority"], "P1")
        self.assertEqual(routing["decision"], "auto-load")

    def test_high_risk_without_matches_remains_p0(self) -> None:
        routing = build_routing("delete production secrets", [], high_risk=True)
        self.assertEqual(routing["priority"], "P0")


class TestConceptGaps(unittest.TestCase):
    def test_extract_skeleton_loader(self) -> None:
        query = "vamos fazer uma alteração na ui e vamos colocar skeleton-loader"
        candidates = extract_concept_candidates(query)
        self.assertIn("skeleton-loader", candidates)

    def test_ui_is_stopword(self) -> None:
        query = "melhorar a ui do app"
        candidates = extract_concept_candidates(query)
        self.assertNotIn("ui", candidates)

    def test_natural_hyphenated_phrases_are_not_packages(self) -> None:
        candidates = extract_concept_candidates(
            "improve the day-to-day open-source end-to-end workflow"
        )
        self.assertEqual(candidates, [])


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
        self.assertTrue(discover["security"]["requires_network_consent"])
        self.assertEqual(discover["security"]["effect"], "network")
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

    def test_discover_query_redacts_secrets_paths_and_urls(self) -> None:
        result = search_skills(
            "find a skill for deploy token=abc123 C:\\private\\client https://internal.example/path",
            self.manifest,
            domain="devops-git",
        )
        query = result["discover"]["queries"][0]
        self.assertNotIn("abc123", query)
        self.assertNotIn("private", query)
        self.assertNotIn("internal.example", query)
        self.assertLessEqual(len(query), 160)

    def test_ci_query_no_discover(self) -> None:
        result = search_skills(
            "corrigir CI quebrado no pull request",
            self.manifest,
            domain="devops-git",
        )
        self.assertEqual(result["results"][0]["name"], "gh-fix-ci")
        self.assertFalse(result["discover"]["triggered"])

    def test_bypass_routing(self) -> None:
        result = search_skills("oi", self.manifest)
        self.assertEqual(result["routing"]["priority"], "P3")
        self.assertEqual(result["routing"]["decision"], "bypass")
        self.assertFalse(result["discover"]["triggered"])

    def test_explicit_domain_is_a_soft_signal_not_a_hard_filter(self) -> None:
        manifest = {
            "version": 4,
            "skills": [
                {
                    "name": "ui-ux-pro-max",
                    "folder": "ui-ux-pro-max",
                    "description": "Design SaaS dashboard UI and accessible web interfaces",
                    "tags": ["dashboard", "ui", "design"],
                    "domain": "web",
                    "path": "/skills/ui-ux-pro-max/SKILL.md",
                    "scope": "agents",
                    "installed": True,
                },
                {
                    "name": "codebase-design",
                    "folder": "codebase-design",
                    "description": "Design deep code modules and seams",
                    "tags": ["architecture"],
                    "domain": "design",
                    "path": "/skills/codebase-design/SKILL.md",
                    "scope": "agents",
                    "installed": True,
                },
                {
                    "name": "tdd",
                    "folder": "tdd",
                    "description": "Test driven development",
                    "tags": ["tests"],
                    "domain": "design",
                    "path": "/skills/tdd/SKILL.md",
                    "scope": "agents",
                    "installed": True,
                },
                {
                    "name": "grilling",
                    "folder": "grilling",
                    "description": "Interview a user about a plan",
                    "tags": [],
                    "domain": "design",
                    "path": "/skills/grilling/SKILL.md",
                    "scope": "agents",
                    "installed": True,
                },
            ],
        }
        result = search_skills("design a SaaS dashboard UI", manifest, domain="design")
        self.assertEqual(result["results"][0]["name"], "ui-ux-pro-max")
        scores = [entry["score"] for entry in result["results"]]
        if len(scores) > 1:
            self.assertGreater(len(set(scores)), 1)

    def test_portuguese_architecture_request_finds_architecture_skill(self) -> None:
        manifest = {
            "version": 4,
            "skills": [
                {
                    "name": "improve-codebase-architecture",
                    "folder": "improve-codebase-architecture",
                    "description": "Scan a codebase for architecture deepening opportunities and usability improvements",
                    "tags": ["architecture", "codebase"],
                    "domain": "meta",
                    "path": "/skills/improve-codebase-architecture/SKILL.md",
                    "scope": "agents",
                    "installed": True,
                },
                {
                    "name": "writing-great-skills",
                    "folder": "writing-great-skills",
                    "description": "Write clear skill documentation",
                    "tags": [],
                    "domain": "meta",
                    "path": "/skills/writing-great-skills/SKILL.md",
                    "scope": "agents",
                    "installed": True,
                },
            ],
        }
        result = search_skills(
            "analisar todo o repositorio e melhorar arquitetura e usabilidade",
            manifest,
        )
        self.assertEqual(
            result["results"][0]["name"], "improve-codebase-architecture"
        )

    def test_namespaced_ci_skill_beats_general_github_router(self) -> None:
        manifest = {
            "version": 4,
            "skills": [
                {
                    "name": "github:gh-fix-ci",
                    "folder": "gh-fix-ci",
                    "description": "Debug and fix failing GitHub PR checks in GitHub Actions",
                    "tags": ["ci", "fix"],
                    "domain": "devops-git",
                    "path": "/plugins/github/gh-fix-ci/SKILL.md",
                    "scope": "codex-plugin",
                    "installed": True,
                },
                {
                    "name": "github:github",
                    "folder": "github",
                    "description": "General GitHub repository and pull request orientation",
                    "tags": ["github"],
                    "domain": "devops-git",
                    "path": "/plugins/github/github/SKILL.md",
                    "scope": "codex-plugin",
                    "installed": True,
                },
            ],
        }
        result = search_skills("corrigir CI quebrado no pull request", manifest)
        self.assertEqual(result["results"][0]["name"], "github:gh-fix-ci")


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


if __name__ == "__main__":
    unittest.main()
