"""Tests for manifest frontmatter and declared domain handling."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "maestro" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_manifest import parse_frontmatter, resolve_skill_domain  # noqa: E402


class TestManifestFrontmatter(unittest.TestCase):
    def test_folded_description_does_not_include_yaml_marker(self) -> None:
        metadata = parse_frontmatter(
            """---
name: example-skill
description: >-
  First description line.
  Second description line.
domain: general
---
"""
        )

        self.assertEqual(
            metadata["description"],
            "First description line. Second description line.",
        )

    def test_literal_description_preserves_line_break(self) -> None:
        metadata = parse_frontmatter(
            """---
name: example-skill
description: |-
  First line.
  Second line.
---
"""
        )

        self.assertEqual(metadata["description"], "First line.\nSecond line.")


class TestDeclaredDomain(unittest.TestCase):
    def test_valid_declared_domain_overrides_text_inference(self) -> None:
        domain = resolve_skill_domain(
            "software-system-blueprint",
            "dashboard chart visualization design",
            "general",
        )

        self.assertEqual(domain, "general")

    def test_security_alias_is_preserved(self) -> None:
        domain = resolve_skill_domain("threat-review", "review threats", "cybersecurity")

        self.assertEqual(domain, "security")

    def test_invalid_domain_falls_back_to_inference(self) -> None:
        domain = resolve_skill_domain(
            "dashboard-design",
            "dashboard chart visualization",
            "software-engineering",
        )

        self.assertEqual(domain, "data-viz")


if __name__ == "__main__":
    unittest.main()
