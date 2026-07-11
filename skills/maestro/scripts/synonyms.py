#!/usr/bin/env python3
"""Query expansion synonyms for maestro skill search (EN + PT partial)."""

from __future__ import annotations

import re
import unicodedata

DEFAULT_SYNONYMS: dict[str, list[str]] = {
    "test": ["teste", "testes", "unitario", "unittest", "falhando", "failing"],
    "debug": ["depurar", "depuracao", "bug", "erro", "root cause", "raiz", "falha"],
    "build": ["compilar", "build", "construir"],
    "fix": ["corrigir", "consertar", "quebrado", "broken"],
    "review": ["revisar", "revisao", "code review", "auditoria"],
    "audit": ["auditoria", "auditar"],
    "design": ["design", "ui", "ux", "interface", "layout", "visual"],
    "dashboard": ["painel", "dashboard", "grafico"],
    "security": ["seguranca", "cybersecurity", "infosec"],
    "forensics": ["forense", "forensics", "volatility", "memoria"],
    "deploy": ["deploy", "publicar", "implantar"],
    "github": ["git", "pull request", "pr", "ci", "actions"],
    "docs": ["documentacao", "readme", "documentar"],
    "architecture": ["arquitetura", "codebase", "estrutura do codigo", "estrutura do código"],
    "repository": ["repositorio", "repositório", "repo"],
    "improve": ["melhorar", "melhoria", "aprimorar", "otimizar"],
    "usability": ["usabilidade", "developer experience", "experiencia do programador", "experiência do programador"],
    "routing": ["roteamento", "orquestracao", "orquestração"],
    "auth": ["autenticacao", "login", "oauth"],
    "skill": ["skill", "habilidade"],
    "superdesign": ["superdesign", "design system"],
}


def expand_query(text: str, extra: dict[str, list[str]] | None = None) -> str:
    """Append canonical terms when synonym phrases appear in the query."""
    synonyms = {**DEFAULT_SYNONYMS, **(extra or {})}
    lowered = _normalize(text)
    extra_terms: list[str] = []

    for canonical, values in synonyms.items():
        canon = _normalize(canonical)
        if _contains_phrase(lowered, canon):
            extra_terms.append(canon)
            continue
        for value in values:
            value_text = _normalize(value).strip()
            if value_text and _contains_phrase(lowered, value_text):
                extra_terms.append(canon)
                break

    if not extra_terms:
        return text
    return f"{text} {' '.join(sorted(set(extra_terms)))}"


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", str(text).casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _contains_phrase(text: str, phrase: str) -> bool:
    pattern = r"(?<!\w)" + re.escape(phrase).replace(r"\ ", r"\s+") + r"(?!\w)"
    return re.search(pattern, text) is not None
