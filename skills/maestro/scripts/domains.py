#!/usr/bin/env python3
"""Domain taxonomy and classification for maestro."""

from __future__ import annotations

import re
import unicodedata

DOMAINS: list[str] = [
    "web",
    "data-viz",
    "analytics",
    "design",
    "creative",
    "devops-git",
    "video-media",
    "integrations",
    "security",
    "meta",
    "general",
]

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "web": [
        "react", "nextjs", "next.js", "frontend", "backend", "api", "typescript",
        "javascript", "shadcn", "stripe", "supabase", "postgres", "tailwind",
        "component", "browser", "remix", "vue", "svelte",
        "html", "css", "web app", "full-stack", "auth", "payment",
    ],
    "data-viz": [
        "chart", "visualization", "dashboard", "d3", "canvas", "threejs",
        "geospatial", "gantt", "diagram", "scrollytelling", "plot",
        "svg", "webgl", "painel",
    ],
    "analytics": [
        "data quality", "kpi", "jupyter", "notebook", "metric", "report",
        "analytics", "business context", "market sizing", "validate data",
        "pandas", "sql", "spreadsheet", "excel",
    ],
    "design": [
        "prototype", "ideate", "design audit", "design qa", "ux research", "figma",
        "mockup", "wireframe", "ui", "ux", "product design", "url-to-code",
        "image-to-code", "user flow", "onboarding", "superdesign", "design system",
        "user interface", "layout",
    ],
    "security": [
        "security", "cybersecurity", "forensics", "malware", "pentest",
        "penetration", "threat", "incident response", "mitre", "attack",
        "vulnerability", "siem", "dfir", "red team", "blue team", "seguranca",
        "forense", "volatility",
    ],
    "creative": [
        "moodboard", "logo", "ads", "brand", "creative", "shot", "scene",
        "positioning", "offer", "generative polish", "explorer",
    ],
    "devops-git": [
        "github", "git", "pull request", "ci", "cd", "commit", "merge",
        "workflow", "actions", "yeet", "fix ci", "address comments",
        "failing check", "actions check", "quebrado", "falhando", "pipeline",
    ],
    "video-media": [
        "remotion", "video", "animation", "render", "composition", "ffmpeg",
        "media", "audio",
    ],
    "integrations": [
        "twilio", "zoom", "slack", "notion", "airtable", "jira", "linear",
        "stripe api", "webhook", "oauth", "sdk", "mcp", "salesforce",
        "hubspot", "intercom",
    ],
    "meta": [
        "skill creator", "skill installer", "plugin creator", "create skill",
        "openai docs", "imagegen", "context7", "documentation library",
        "architecture", "arquitetura", "codebase", "repository", "repositorio",
        "repositório", "refactor", "refatorar", "routing", "roteamento",
        "orchestration", "orquestracao", "orquestração",
    ],
}

NAME_PREFIX_DOMAIN: list[tuple[str, str]] = [
    ("build-web-data-visualization-", "data-viz"),
    ("data-analytics-", "analytics"),
    ("product-design-", "design"),
    ("creative-production-", "creative"),
    ("gh-", "devops-git"),
    ("netlify-", "web"),
    ("twilio-", "integrations"),
    ("zoom-", "integrations"),
    ("figma-", "design"),
    ("codex-", "meta"),
]

HUB_SKILLS: set[str] = {
    "index",
    "product-design-index",
    "data-visualization",
    "build-web-data-visualization-data-visualization",
    "explore",
}


def _text_blob(name: str, description: str) -> str:
    return _normalize(f"{name} {description}")


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", str(text).casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _contains_keyword(text: str, keyword: str) -> bool:
    normalized_text = _normalize(text)
    normalized_keyword = _normalize(keyword).strip()
    if not normalized_keyword:
        return False
    pattern = r"(?<!\w)" + re.escape(normalized_keyword).replace(r"\ ", r"\s+") + r"(?!\w)"
    return re.search(pattern, normalized_text) is not None


def classify_skill(name: str, description: str) -> str:
    if name.lower() == "superdesign":
        return "design"

    blob = _text_blob(name, description)
    for prefix, domain in NAME_PREFIX_DOMAIN:
        if name.lower().startswith(prefix):
            return domain

    scores = {domain: 0 for domain in DOMAINS}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if _contains_keyword(blob, kw):
                scores[domain] += 1

    best_score = max(scores.values())
    if best_score > 0:
        winners = [domain for domain, score in scores.items() if score == best_score]
        return winners[0] if len(winners) == 1 else "general"
    return "general"


def classify_query(query: str) -> tuple[str, dict[str, int]]:
    scores = {domain: 0 for domain in DOMAINS}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if _contains_keyword(query, kw):
                scores[domain] += 1

    best_score = max(scores.values())
    if best_score == 0:
        return "general", scores
    winners = [domain for domain, score in scores.items() if score == best_score]
    return (winners[0] if len(winners) == 1 else "general"), scores


def domain_label(domain: str) -> str:
    labels = {
        "web": "Web / apps",
        "data-viz": "Data visualization",
        "analytics": "Data analytics",
        "design": "Product design",
        "creative": "Creative production",
        "devops-git": "Git / CI / DevOps",
        "video-media": "Video / media",
        "integrations": "Integrations / SDKs",
        "security": "Cybersecurity",
        "meta": "Meta / tooling",
        "general": "General",
    }
    return labels.get(domain, domain)
