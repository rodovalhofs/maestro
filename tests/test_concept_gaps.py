"""Unit tests for concept gap detection."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "maestro" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from concept_gaps import (  # noqa: E402
    MAX_DISCOVER_GAPS,
    build_discover_queries,
    extract_concept_candidates,
    find_concept_gaps,
)
from search_skills import skill_document  # noqa: E402
from synonyms import expand_query  # noqa: E402


class TestConceptGapLimits(unittest.TestCase):
    def test_max_two_gaps_with_notes(self) -> None:
        query = (
            "colocar skeleton-loader e react-query e tanstack-table na ui"
        )
        candidates = extract_concept_candidates(query)
        self.assertGreater(len(candidates), MAX_DISCOVER_GAPS)

        pool = [
            {
                "name": "react-best-practices",
                "folder": "react-best-practices",
                "description": "React patterns",
                "tags": ["react"],
                "domain": "web",
            }
        ]
        results = [
            {
                "name": "react-best-practices",
                "description": "React patterns",
                "tags": ["react"],
            }
        ]
        gaps, notes = find_concept_gaps(
            query, results, pool, skill_document, expand_query
        )
        self.assertLessEqual(len(gaps), MAX_DISCOVER_GAPS)
        self.assertTrue(notes)

    def test_build_discover_queries_includes_gap(self) -> None:
        queries = build_discover_queries(
            ["skeleton-loader"],
            "vamos colocar skeleton-loader na ui",
            "web",
        )
        self.assertEqual(len(queries), 1)
        self.assertIn("skeleton-loader", queries[0])


if __name__ == "__main__":
    unittest.main()
