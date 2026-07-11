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

## Search and route

```bash
npx maestro-skills search "dashboard react"
npx maestro-skills search "fix CI" --domain devops-git --project-root . --json
npx maestro-skills route --task "design UI" --task "fix CI" --json
```

`search` and `route` print compact text by default. `--json` is the stable automation
surface. `--domain` is a ranking hint, not a hard filter.

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
