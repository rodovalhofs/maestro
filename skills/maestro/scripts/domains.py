#!/usr/bin/env python3
"""Domain taxonomy and classification for maestro."""

from __future__ import annotations

import re

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
        "component", "browser", "testing", "debug", "remix", "vue", "svelte",
        "html", "css", "web app", "full-stack", "auth", "payment",
    ],
    "data-viz": [
        "chart", "graph", "visualization", "dashboard", "d3", "canvas", "threejs",
        "geospatial", "map", "gantt", "diagram", "scrollytelling", "plot",
        "accessibility", "svg", "webgl", "painel",
    ],
    "analytics": [
        "data quality", "kpi", "jupyter", "notebook", "metric", "report",
        "analytics", "business context", "market sizing", "validate data",
        "pandas", "sql", "spreadsheet", "excel",
    ],
    "design": [
        "prototype", "ideate", "audit", "design qa", "ux research", "figma",
        "mockup", "wireframe", "ui", "ux", "product design", "url-to-code",
        "image-to-code", "user flow", "onboarding", "superdesign", "design system",
        "interface", "layout",
    ],
    "security": [
        "security", "cybersecurity", "forensics", "malware", "pentest",
        "penetration", "threat", "incident response", "mitre", "attack",
        "vulnerability", "siem", "dfir", "red team", "blue team", "seguranca",
        "segurança", "ciberseguranca", "cibersegurança", "forense", "volatility",
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

SECURITY_SAFE_EXECUTION_PATTERNS: list[str] = [
    r"\bcom\s+seguran[cç]a\b",
]


def _text_blob(name: str, description: str) -> str:
    return f"{name} {description}".lower()


def contains_keyword(text: str, keyword: str) -> bool:
    """Match taxonomy terms as words/phrases instead of arbitrary substrings."""
    return re.search(
        rf"(?<!\w){re.escape(keyword.lower())}(?!\w)",
        text.lower(),
    ) is not None


def strip_safe_execution_phrases(text: str) -> str:
    normalized = text
    for pattern in SECURITY_SAFE_EXECUTION_PATTERNS:
        normalized = re.sub(pattern, " ", normalized, flags=re.IGNORECASE)
    return normalized


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
            if contains_keyword(blob, kw):
                scores[domain] += 1

    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best
    return "general"


def classify_query(query: str) -> tuple[str, dict[str, int]]:
    query_lower = query.lower()
    security_query = strip_safe_execution_phrases(query_lower)

    scores = {domain: 0 for domain in DOMAINS}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        searchable = security_query if domain == "security" else query_lower
        for kw in keywords:
            if contains_keyword(searchable, kw):
                scores[domain] += 1

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "general", scores
    return best, scores


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
