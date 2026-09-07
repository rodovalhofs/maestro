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
from bm25 import BM25  # noqa: E402
from domains import classify_query  # noqa: E402
from intents import is_bypass_task, is_force_discover, task_intents  # noqa: E402
from routing import build_routing, is_high_risk, select_mode  # noqa: E402
from route_tasks import route_batch  # noqa: E402
from search_skills import metadata_match_boost, search_skills, skill_document  # noqa: E402
from synonyms import expand_query  # noqa: E402

FIXTURE_MANIFEST = Path(__file__).parent / "fixtures" / "sample-manifest.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE_MANIFEST.read_text(encoding="utf-8"))


class UpstreamTestTextNormalization(unittest.TestCase):

    def test_bm25_matches_accented_and_unaccented_text(self) -> None:
        bm25 = BM25()
        bm25.fit(["mudança código segurança"])

        accented = bm25.score("mudança código segurança")[0][1]
        unaccented = bm25.score("mudanca codigo seguranca")[0][1]

        self.assertGreater(accented, 0)
        self.assertAlmostEqual(accented, unaccented)

    def test_metadata_phrase_match_respects_token_boundaries(self) -> None:
        boost, matches = metadata_match_boost(
            "encode smells in a diagnostic payload",
            {
                "name": "unrelated-skill",
                "folder": "unrelated-skill",
                "tags": ["code-smells"],
            },
        )

        self.assertEqual(0.0, boost)
        self.assertEqual([], matches)

    def test_metadata_boost_does_not_accumulate_with_tag_quantity(self) -> None:
        boost, matches = metadata_match_boost(
            "diagnose code smells",
            {
                "name": "unrelated-skill",
                "folder": "unrelated-skill",
                "tags": ["code-smells", "code_smells", "code smells"],
            },
        )

        self.assertEqual(3.0, boost)
        self.assertEqual(3, len(matches))

class UpstreamTestDomains(unittest.TestCase):

    def test_safe_execution_phrase_is_not_cybersecurity(self) -> None:
        for query in (
            "refatorar codigo legado com seguranca",
            "refatorar código legado com segurança",
        ):
            domain, scores = classify_query(query)
            self.assertNotEqual(domain, "security")
            self.assertEqual(scores["security"], 0)

    def test_explicit_security_context_remains_security(self) -> None:
        domain, scores = classify_query(
            "revisar segurança da aplicação e vulnerabilidades"
        )
        self.assertEqual(domain, "security")
        self.assertGreater(scores["security"], 0)

    def test_short_keywords_do_not_match_inside_portuguese_words(self) -> None:
        domain, scores = classify_query("entender requisitos e regras de negócio")
        self.assertEqual(domain, "general")
        self.assertEqual(scores["design"], 0)
        self.assertEqual(scores["devops-git"], 0)

class UpstreamTestConceptGaps(unittest.TestCase):

    def test_generic_change_is_not_a_concept_gap_candidate(self) -> None:
        for query in (
            "implementar mudança local com testes",
            "implementar mudanca local com testes",
            "implement change safely",
        ):
            self.assertEqual([], extract_concept_candidates(query))

class UpstreamTestSearchSkills(unittest.TestCase):

    def setUp(self) -> None:
        self.manifest = load_fixture()

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
                    "scope": "agents",
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

        self.assertNotEqual(result["domain"], "security")
        self.assertEqual(result["results"][0]["name"], "safe-refactoring")

    def test_complete_tag_match_outranks_incidental_description_terms(self) -> None:
        manifest = {
            "version": 4,
            "skills": [
                {
                    "name": "clean-code-implementation",
                    "folder": "clean-code-implementation",
                    "description": (
                        "Implementar ou melhorar uma mudança local com código legível; "
                        "usar ao alterar funções e erros"
                    ),
                    "tags": ["codigo-limpo", "clean-code", "implementacao"],
                    "domain": "general",
                    "path": "/tmp/clean-code/SKILL.md",
                    "scope": "agents",
                },
                {
                    "name": "code-smell-detection",
                    "folder": "code-smell-detection",
                    "description": (
                        "Detectar e priorizar deterioração com evidências; não modificar código"
                    ),
                    "tags": ["maus-cheiros", "code-smells", "diagnostico"],
                    "domain": "general",
                    "path": "/tmp/code-smells/SKILL.md",
                    "scope": "agents",
                },
                {
                    "name": "safe-refactoring",
                    "folder": "safe-refactoring",
                    "description": "Refatorar código preservando comportamento",
                    "tags": ["refatoracao", "legacy-code"],
                    "domain": "general",
                    "path": "/tmp/refactoring/SKILL.md",
                    "scope": "agents",
                },
            ]
        }

        result = search_skills(
            "diagnosticar code smells sem alterar codigo",
            manifest,
            domain="general",
        )

        self.assertEqual("code-smell-detection", result["results"][0]["name"])
        self.assertEqual(3.0, result["results"][0]["metadata_boost"])
        self.assertIn("tag:code-smells", result["results"][0]["metadata_matches"])
        self.assertFalse(result["weak_match"])
        self.assertFalse(result["discover"]["triggered"])

    def test_auto_detected_domain_also_considers_general_skills(self) -> None:
        manifest = {
            "version": 4,
            "skills": [
                {
                    "name": "modular-system-architecture",
                    "folder": "modular-system-architecture",
                    "description": (
                        "Design a modular and maintainable backend with module "
                        "responsibilities and explicit dependencies"
                    ),
                    "tags": ["modular-architecture", "backend", "maintainability"],
                    "domain": "general",
                    "path": "/tmp/modular/SKILL.md",
                    "scope": "agents",
                    "installed": True,
                },
                *[
                    {
                        "name": f"web-helper-{index}",
                        "folder": f"web-helper-{index}",
                        "description": "Build a web backend application",
                        "tags": ["web", "backend"],
                        "domain": "web",
                        "path": f"/tmp/web-{index}/SKILL.md",
                        "scope": "agents",
                        "installed": True,
                    }
                    for index in range(3)
                ],
            ]
        }

        result = search_skills(
            "design a modular and maintainable backend",
            manifest,
        )

        self.assertEqual(result["detected_domain"], "web")
        self.assertEqual(result["results"][0]["name"], "modular-system-architecture")

class UpstreamTestRouteBatch(unittest.TestCase):

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
