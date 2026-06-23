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
        "accessibility", "svg", "webgl",
    ],
    "analytics": [
        "data quality", "kpi", "jupyter", "notebook", "metric", "report",
        "analytics", "business context", "market sizing", "validate data",
        "pandas", "sql", "spreadsheet", "excel",
    ],
    "design": [
        "prototype", "ideate", "audit", "design qa", "ux research", "figma",
        "mockup", "wireframe", "ui", "ux", "product design", "url-to-code",
        "image-to-code", "user flow", "onboarding",
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


def _text_blob(name: str, description: str) -> str:
    return f"{name} {description}".lower()


def classify_skill(name: str, description: str) -> str:
    blob = _text_blob(name, description)
    for prefix, domain in NAME_PREFIX_DOMAIN:
        if name.lower().startswith(prefix):
            return domain

    scores = {domain: 0 for domain in DOMAINS}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw in blob:
                scores[domain] += 1

    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best
    return "general"


def classify_query(query: str) -> tuple[str, dict[str, int]]:
    query_lower = query.lower()
    scores = {domain: 0 for domain in DOMAINS}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
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
        "meta": "Meta / tooling",
        "general": "General",
    }
    return labels.get(domain, domain)
