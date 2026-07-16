#!/usr/bin/env python3
"""Query expansion synonyms for maestro skill search (EN + PT partial)."""

from __future__ import annotations

import re

DEFAULT_SYNONYMS: dict[str, list[str]] = {
    "test": ["teste", "testes", "unitario", "unittest", "falhando", "failing"],
    "debug": ["depurar", "depuracao", "bug", "erro", "root cause", "raiz", "falha"],
    "build": ["compilar", "build", "construir"],
    "review": ["revisar", "revisao", "code review", "auditoria"],
    "audit": ["auditoria", "auditar"],
    "design": ["design", "ui", "ux", "interface", "layout", "visual"],
    "dashboard": ["painel", "dashboard", "grafico"],
    "security": ["seguranca", "cybersecurity", "infosec"],
    "forensics": ["forense", "forensics", "volatility", "memoria"],
    "deploy": ["deploy", "publicar", "implantar"],
    "github": ["git", "pull request", "pr", "ci", "actions"],
    "docs": ["documentacao", "readme", "documentar"],
    "auth": ["autenticacao", "login", "oauth"],
    "skill": ["skill", "habilidade"],
    "superdesign": ["superdesign", "design system"],
}


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(
        rf"(?<!\w){re.escape(phrase.lower())}(?!\w)",
        text.lower(),
    ) is not None


def expand_query(text: str, extra: dict[str, list[str]] | None = None) -> str:
    """Append canonical terms when synonym phrases appear in the query."""
    synonyms = {**DEFAULT_SYNONYMS, **(extra or {})}
    lowered = text.lower()
    tokens = set(re.findall(r"[a-z0-9]{3,}", lowered))
    extra_terms: list[str] = []

    for canonical, values in synonyms.items():
        canon = canonical.lower()
        if canon in tokens or canon in lowered:
            extra_terms.append(canon)
            continue
        for value in values:
            value_text = value.lower().strip()
            if value_text and _contains_phrase(lowered, value_text):
                extra_terms.append(canon)
                break

    if not extra_terms:
        return text
    return f"{text} {' '.join(sorted(set(extra_terms)))}"
