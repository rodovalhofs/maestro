<div align="center">

# Maestro

**Local-first skill routing for AI coding agents**

Prepare an approved specification, compare skill instructions against project
evidence, and execute the complete objective through validated phases.

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
- Evidence-based: ranking finds candidates; the agent reads instructions before choosing.
- Integrated preparation: Prompt Designer works with grilling in the same conversation and saves a local specification.
- Targeted research: the agent researches confirmed gaps with public technical terms; installation requires approval.
- Human-controlled: graph approval and existing effect-specific authorizations govern execution.
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
conversation + approved spec + project evidence
  -> project-aware metadata retrieval (BM25 + intents + domain hint)
  -> read candidate SKILL.md -> compare objective / phase / compatibility / restrictions
  -> research confirmed gaps -> explain selection -> graph approval -> validated phases
```

The catalog stores declared skill metadata and local paths. Missing descriptions do
not cause arbitrary `SKILL.md` body content to be copied into the manifest. Duplicate
skills retain all locations while selecting one canonical path by scope priority.

The CLI remains offline. The agent researches confirmed gaps or explicitly requested
alternatives unless the user prohibits network access. Suggested external queries
are assembled from reviewed public technical vocabulary, never raw user prose.
Unknown terms require agent review. Installation still requires explicit approval.

Retrieval scores are uncalibrated and never authorize automatic loading. Version
0.3.0 replaces the old JSON `confidence` field with `evidence`; routing decisions
are `review-candidates`, `compare-candidates`, `no-match` or `bypass`. Consumers must
perform content review before selection. See [CLI migration](docs/maestro-skills-cli.md).

## Prepare and execute in one conversation

Setup installs both `maestro` and `maestro-prompt-designer` in each selected target.
Use your existing grilling skill with Prompt Designer to resolve decisions one at
a time. Grilling is optional and is not redistributed by this package.

```text
Use grilling with maestro-prompt-designer to clarify this task.
[Discuss and approve the specification.]
$maestro execute the approved specification.
```

The spec stays under `<project>/.maestro/specs/<task>.md`, outside npm archives.
Maestro reuses the conversation and spec; there is no need to paste them again.
For full projects, it retains later phases until all requested acceptance criteria
are satisfied. Relevant missing decisions may still require clarification.

## Local data

The CLI writes to installation targets and `~/.maestro/`; Prompt Designer also
saves task specifications in the selected project's `.maestro/specs/`:

```text
~/.maestro/
├── config.json                  # versioned multi-project install registry
├── skills-manifest.json         # local skill metadata and provenance
├── maestro-exclude.txt          # local search exclusions
├── skill-runbooks.user.json     # user runbooks
└── discover-allowlist.txt       # reviewed remote repositories
```

Project runbooks may live at `<project>/.maestro/skill-runbooks.json`. User/project
preflights and side-effecting preflights require applicable authorization. See
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
python scripts/evaluate-routing.py
```

Release inputs are explicitly listed in `scripts/release-layout.mjs`. Verification
packs and scans actual tar contents, checks the exact inventory and SHA-512 integrity,
and rejects unexpected files, symbolic links, common secret formats and personal paths.
This complements human privacy review; it does not prove that arbitrary text contains
no private information. Use `node scripts/verify-packages.mjs --keep` to retain inspected
archives under `artifacts/release/`. No local code change implies publication permission.
