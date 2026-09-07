"""Build external queries from public vocabulary; never send raw user prose.

Unknown technologies require an agent-authored public technical query after review.
"""
import re
from synonyms import _normalize

PUBLIC_TERMS = {
    "react", "next.js", "vue", "angular", "svelte", "astro", "typescript",
    "javascript", "python", "godot", "gdscript", "phaser", "unity", "unreal",
    "rust", "golang", "java", "kotlin", "swift", "ruby", "rails", "django",
    "fastapi", "flask", "express", "node.js", "npm", "docker", "kubernetes",
    "postgresql", "mysql", "sqlite", "redis", "mongodb", "supabase", "prisma",
    "aws", "azure", "cloudflare", "terraform", "github", "gitlab", "ci",
    "debug", "test", "testing", "review", "audit", "architecture", "security",
    "performance", "accessibility", "frontend", "backend", "dashboard", "ui",
    "ux", "design", "animation", "sprite", "multiplayer", "networking",
    "forensics", "volatility", "authentication", "oauth", "deploy", "docs",
    "routing", "refactoring", "requirements", "planning", "observability",
    "skeleton-loader", "react-query", "tanstack-table", "shadcn", "tailwind",
    "changelog", "remotion", "blender", "three.js", "webgl", "figma",
}


def technical_query(text: str, max_terms: int = 6) -> str:
    # Remove sensitive spans before recognizing otherwise-public words.
    text = re.sub(r"https?://\S+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", " ", text)
    text = re.sub(r"[A-Za-z]:[\\/]\S+|(?<!\w)[/~]?[\w.-]+(?:[/\\][\w.-]+)+", " ", text)
    text = re.sub(r"(?i)\b(?:token|password|passwd|secret|api[_-]?key|credential|senha)\s*[:=]\s*(?:\"[^\"]*\"|'[^']*'|\S+)", " ", text)
    text = _normalize(text)
    found = []
    for term in PUBLIC_TERMS:
        match = re.search(r"(?<![\w.-])" + re.escape(term) + r"(?![\w.-])", text)
        if match:
            found.append((match.start(), term))
    return " ".join(term for _, term in sorted(found)[:max_terms])
