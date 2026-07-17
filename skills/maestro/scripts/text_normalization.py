#!/usr/bin/env python3
"""Shared Unicode normalization for Maestro search and gap detection."""

from __future__ import annotations

import re
import unicodedata


def fold_text(value: object) -> str:
    """Return case-folded text without diacritics, preserving separators."""
    decomposed = unicodedata.normalize("NFKD", str(value).casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def search_tokens(value: object) -> list[str]:
    """Tokenize text consistently across queries, metadata, and documents."""
    normalized = fold_text(value).replace("_", " ")
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    return [token for token in normalized.split() if len(token) > 2]


def searchable_phrase(value: object) -> str:
    """Normalize text to a whitespace-separated phrase for exact matching."""
    return " ".join(search_tokens(value))
