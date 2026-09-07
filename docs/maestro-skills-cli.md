# `maestro-skills` CLI

The CLI installs, indexes, searches, diagnoses, and removes Maestro locally. The
scoped package `@rodovalhofs/maestro` exposes the same surface through the `maestro`
binary.

## Setup

```bash
npx maestro-skills setup
npx maestro-skills setup --codex --cursor -y
npx maestro-skills setup --project --codex -y
```

Without target flags, interactive setup shows available destinations. `-y` selects
only detected agents; it does not silently install into every supported directory.
The registry at `~/.maestro/config.json` preserves global and per-project records.
Setup installs and upgrades both Maestro and Prompt Designer as a transaction per
agent. Removal deletes only the skills recorded for that installation; legacy
records do not imply ownership of a separately installed Prompt Designer.

## Search and route

```bash
npx maestro-skills search "dashboard react"
npx maestro-skills search "fix CI" --domain devops-git --project-root . --json
npx maestro-skills route --task "design UI" --task "fix CI" --json
```

`search` and `route` print compact text by default. `--json` is the stable automation
surface. `--domain` is a ranking hint, not a hard filter.
Both default to the current project and accept `--project-root <path>`. Both accept
`--local-only` to disable external research suggestions. Their processes never
perform remote research themselves; the agent follows the skill's research workflow.

## Migration to 0.3.0

The CLI command names are unchanged. JSON consumers must adapt to:

- `results[].confidence` removed: use `evidence.matched_terms`, `query_coverage`,
  `source` and `content_reviewed` for retrieval evidence, not a probability.
- `routing.decision`: `review-candidates`, `compare-candidates`, `no-match`, `bypass`
  (`recommend` can occur on an aggregate high-risk batch).
- `routing.load_limit` is zero. `review_limit` bounds candidate reading, and
  `requires_content_review` prevents treating metadata ranking as a final choice.
- `selection` lists the content-review criteria, candidate paths and local spec
  directory. The agent reads files; the CLI does not pretend to understand their body.
- `discover.queries` contains only known public technical vocabulary. Empty queries
  require agent review, never fallback to the raw prompt. `enabled` honors local-only.
- Network research on a confirmed gap is allowed by the skill unless the user
  prohibits it. This is distinct from installation authorization.

`score`, `query_coverage` and `relative_margin` are uncalibrated lexical signals.
Two close candidates need content comparison before deciding whether to ask the user.
The 0.3.0 release includes a curated bilingual regression benchmark; it does not
establish production accuracy or guarantee an agent's semantic judgment.

`route` also accepts newline-delimited stdin:

```bash
printf "design UI\nfix CI\n" | npx maestro-skills route --json
```

## Manifest and diagnostics

```bash
npx maestro-skills manifest --project-root .
npx maestro-skills doctor
npx maestro-skills doctor --json
```

`doctor` checks Python, the bundled skill, manifest JSON, installation records, and
user runbooks. It is read-only and does not use the network.

## Runbooks

```bash
npx maestro-skills runbook list
npx maestro-skills runbook add my-skill --summary "Lint" --notes "Run before changes"
npx maestro-skills runbook edit my-skill
npx maestro-skills runbook init-allowlist
```

Files merge from bundled `skill-runbooks.json`, then
`~/.maestro/skill-runbooks.user.json`, then `<project>/.maestro/skill-runbooks.json`.
Invalid files are reported and skipped.

## Remove

```bash
npx maestro-skills remove
npx maestro-skills remove --project . -y
npx maestro-skills remove --all -y
npx maestro-skills remove --all -y --clean-home
```

`--project [path]` removes only that registered project. `--clean-home` deletes only
known Maestro files, not the home directory or unrelated files.

## Supported destinations

| Agent | Global skill directory | Flag |
|-------|------------------------|------|
| Cursor | `~/.cursor/skills` | `--cursor` |
| Claude Code | `~/.claude/skills` | `--claude` |
| Codex | `~/.codex/skills` | `--codex` |
| Universal | `~/.agents/skills` | `--universal` |

## PowerShell adapter

Prefer the npm CLI. When calling an installed script directly, use PowerShell's call
operator and `$env:USERPROFILE`:

```powershell
& "$env:USERPROFILE\.codex\skills\maestro\scripts\invoke.ps1" search "fix CI" --json
```

## Exit behavior

- `0`: success;
- `1`: invalid request or failed health check;
- `2`: catalog unavailable/invalid;
- `127`: Python unavailable.

Errors include remediation and avoid Python tracebacks for expected user failures.
