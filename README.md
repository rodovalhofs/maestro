<div align="center">

# Maestro

**Local-first skill routing for AI coding agents**

Search installed skills, inspect an editable dependency graph, and run specialist
agents only after approval.

```bash
npx maestro-skills setup
```

[CLI](docs/maestro-skills-cli.md) · [Security](SECURITY.md) · [Contributing](CONTRIBUTING.md) · [MIT](LICENSE)

</div>

## Why Maestro

Coding agents often accumulate many skills across Cursor, Claude Code, Codex, and
`~/.agents/skills`. Maestro creates one catalog with provenance, ranks the skills
for a prompt, and proposes the smallest useful dependency graph.

- Local-first: search, routing, diagnostics, and manifest generation do not use the network.
- Project-safe: the active project's skills are overlaid at query time; another project's skills do not leak into results.
- Plugin-aware: Codex plugin skills are namespaced, for example `github:gh-fix-ci`.
- Human-controlled: subagents, remote discovery, installation, writes, Git, and publishing remain visible decisions.
- Cross-platform: the npm CLI and Python adapters support Windows, macOS, and Linux.

## Quick start

Requirements: Node.js 18+ and Python 3.10+.

```bash
# Install into detected agent skill directories
npx maestro-skills setup

# Or target agents explicitly
npx maestro-skills setup --codex --cursor -y

# Install only in the current repository
npx maestro-skills setup --project --codex -y

# Verify the local installation
npx maestro-skills doctor
```

Invoke it in your agent:

```text
$maestro improve this repository's architecture and test strategy
$maestro fix the CI failure and explain the root cause
$maestro which installed skills should I use for this dashboard?
```

## CLI

```bash
# Compact output by default; use --json for automation
npx maestro-skills search "dashboard react"
npx maestro-skills search "fix CI" --domain devops-git --json

# Route multiple tasks
npx maestro-skills route --task "design UI" --task "validate accessibility" --json
printf "design UI\nfix CI\n" | npx maestro-skills route --json

# Rebuild and diagnose
npx maestro-skills manifest --project-root .
npx maestro-skills doctor --json

# Manage local runbooks
npx maestro-skills runbook list
npx maestro-skills runbook add my-skill --summary "Local lint" --notes "Run before implementation"

# Remove one project without touching other installations
npx maestro-skills remove --project . -y
```

The scoped package exposes the same commands with a shorter binary:

```bash
npx @rodovalhofs/maestro doctor
```

## How routing works

```text
prompt -> project-aware catalog -> BM25 + intents + domain hint
       -> risk/confidence policy -> ranked skills -> editable DAG -> approval
```

The catalog stores declared skill metadata and local paths. Missing descriptions do
not cause arbitrary `SKILL.md` body content to be copied into the manifest. Duplicate
skills retain all locations while selecting one canonical path by scope priority.

Remote discovery is only a suggestion in the JSON response. Maestro sanitizes the
proposed query and requires consent before any `skills.sh` request. It never installs
a remote skill automatically.

## Local data

Maestro writes only to its installation targets and `~/.maestro/`:

```text
~/.maestro/
├── config.json                  # versioned multi-project install registry
├── skills-manifest.json         # local skill metadata and provenance
├── maestro-exclude.txt          # local search exclusions
├── skill-runbooks.user.json     # user runbooks
└── discover-allowlist.txt       # reviewed remote repositories
```

Project runbooks may live at `<project>/.maestro/skill-runbooks.json`. User/project
preflights and every side-effecting preflight require confirmation. See
[SECURITY.md](SECURITY.md) for the threat model and data boundaries.

## Repository layout

```text
maestro/
├── skills/maestro/              # canonical skill and Python routing engine
├── packages/maestro-skills/     # canonical npm CLI
├── packages/rodovalhofs-maestro/# scoped adapter generated from the canonical CLI
├── tests/                       # Python behavior and security tests
├── docs/                        # user and maintainer documentation
└── scripts/                     # package synchronization and release helpers
```

## Development

```bash
node scripts/sync-skill-to-cli.mjs
python -m unittest discover -s tests -v
npm ci --prefix packages/maestro-skills
npm test --prefix packages/maestro-skills
```

Before publishing, also inspect both package archives:

```bash
npm run verify:packages
```

No repository contribution or local code change implies permission to publish to
npm or push to GitHub.
