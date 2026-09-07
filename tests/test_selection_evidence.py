import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/maestro/scripts"))
from bm25 import BM25
from discovery import technical_query
from route_tasks import route_batch
from search_skills import search_skills


def catalog(descriptions):
    return {"version": 4, "skills": [
        {"name": f"candidate-{i}", "path": f"/skills/candidate-{i}/SKILL.md", "description": text}
        for i, text in enumerate(descriptions)
    ]}


class SelectionEvidenceTests(unittest.TestCase):
    def test_short_technical_terms_and_accents(self):
        engine = BM25()
        engine.fit(["UI UX CI 2D AI", "arquitetura revisão"])
        self.assertEqual(engine.score("UI")[0][0], 0)
        self.assertEqual(engine.score("revisao")[0][0], 1)

    def test_repeating_query_does_not_inflate_score(self):
        engine = BM25()
        engine.fit(["React component performance", "Godot multiplayer"])
        self.assertEqual(engine.score("React"), engine.score("React React React"))

    def test_close_candidates_require_comparison_even_with_one_result_requested(self):
        result = search_skills("React component", catalog(["React component", "React component"]), max_results=1)
        self.assertTrue(result["routing"]["ambiguous"])
        self.assertEqual(result["routing"]["decision"], "compare-candidates")
        self.assertEqual(len(result["results"]), 1)
        self.assertFalse(result["routing"]["execution_authorized"])
        self.assertNotIn("confidence", result["results"][0])
        self.assertFalse(result["results"][0]["evidence"]["content_reviewed"])

    def test_empty_catalog_still_exposes_gap(self):
        result = search_skills("React performance", catalog([]))
        self.assertEqual(result["routing"]["decision"], "no-match")
        self.assertTrue(result["discover"]["triggered"])

    def test_private_prose_is_not_an_outbound_query(self):
        text = "React dashboard for client Northwind acquisition of ConfidentialCompany budget 438829 USD"
        self.assertEqual(technical_query(text), "react dashboard")
        self.assertEqual(technical_query("AcquisitionSecretTenant"), "")
        self.assertEqual(technical_query('token="react dashboard" C:\\private\\python https://private.test/godot'), "")

    def test_local_only_suppresses_outbound_queries(self):
        result = search_skills("find a skill for React", catalog([]), local_only=True)
        self.assertFalse(result["discover"]["enabled"])
        self.assertEqual(result["discover"]["queries"], [])

    def test_greeting_prefix_does_not_bypass_task(self):
        result = search_skills("oi, React component", catalog(["React component"]))
        self.assertNotEqual(result["routing"]["decision"], "bypass")

    def test_batch_uses_only_active_project_overlay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(catalog([])), encoding="utf-8")
            for project, name in [("a", "ui-a"), ("b", "ui-b")]:
                folder = root / project / ".agents/skills" / name
                folder.mkdir(parents=True)
                (folder / "SKILL.md").write_text(f"---\nname: {name}\ndescription: React component design\n---\n", encoding="utf-8")
            result = route_batch(["React component"], manifest, project_root=root / "b")
            names = [skill["name"] for skill in result["results"][0]["results"]]
            self.assertEqual(names, ["ui-b"])

    def test_bilingual_retrieval_regressions(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from importlib import import_module
        evaluate = import_module("evaluate-routing").evaluate
        result = evaluate(search_skills, json.loads((ROOT / "tests/fixtures/routing-benchmark.json").read_text(encoding="utf-8")))
        failures = [item for item in result["results"] if not item["passed"]]
        self.assertEqual(failures, [])
