"""Tests for UTF-8 stdout configuration."""

from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "maestro" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from search_skills import configure_stdout_utf8  # noqa: E402


class TestStdoutUtf8(unittest.TestCase):
    def test_configure_stdout_utf8_replaces_unencodable(self) -> None:
        buffer = io.BytesIO()
        text = io.TextIOWrapper(buffer, encoding="cp1252", errors="strict")
        original = sys.stdout
        sys.stdout = text
        try:
            configure_stdout_utf8()
            print("Preflight design-system \u2192 Implement UI")
            sys.stdout.flush()
            raw = buffer.getvalue()
            self.assertTrue(raw)
        finally:
            sys.stdout = original


if __name__ == "__main__":
    unittest.main()
