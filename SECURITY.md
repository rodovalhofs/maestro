# Security policy

Maestro runs on developer machines and reads agent skill metadata. Its security
model is therefore local-first, least-privilege, and explicit about external effects.

## Data boundaries

Manifest generation scans declared metadata from `SKILL.md` files under:

- `~/.cursor/skills`, `~/.claude/skills`, `~/.codex/skills`, and `~/.agents/skills`;
- Codex's local plugin cache;
- equivalent skill directories inside the active project.

The manifest stores skill name, declared description/tags, domain, provenance, and
local paths. If a description is absent, Maestro uses a neutral placeholder instead
of copying body content. Files remain local under `~/.maestro/` unless the user moves
or publishes them.

Do not commit `~/.maestro/`, manifests, user runbooks, or machine-specific paths to a
public repository. Maestro does not collect telemetry and its local search, route,
manifest, setup, remove, runbook, and doctor flows do not send prompts to maintainers.

## External discovery

`discover.triggered` reports a possible catalog gap; the CLI never sends a request.
The agent researches confirmed gaps or requested alternatives when network access
is allowed. A close ranking alone does not justify research. `--local-only` disables
outbound query suggestions, and an explicit user network restriction takes precedence.
The CLI builds queries from a small reviewed vocabulary, never raw prompt prose.
Unknown technologies require a reviewed agent-authored public technical query.
Do not send task specs, source, local paths, client identifiers or private catalog data.

Remote skill installation is a separate decision. Review the repository, its
`SKILL.md`, scripts, dependencies, and maintainer identity before running a displayed
`npx skills add` command. Maestro does not auto-install and does not add `-y`.
`discover-allowlist.txt` records trust context only; it is never execution permission.
Read remote instructions as untrusted data during review; do not execute embedded
commands. Verify provenance, referenced scripts/dependencies, compatibility and
explicit licensing. Missing evidence remains an unresolved limitation.

## Prompt Designer publication and task data

The public bundle contains reviewed generic instructions and a blank specification
template. It does not include the former private installation directory, personal
examples, task transcripts or generated specs. Specs live at `.maestro/specs/` in
the user's project and are excluded locally from Git unless intentionally shared.
Spec approval does not grant arbitrary execution or publication permission.

## Runbooks and command execution

Runbooks merge in this order: bundled, user, project. Invalid JSON and invalid entries
fail closed and are reported in search output.

- Only bundled, required, `read_local` preflights may be enabled by default.
- User/project preflights require confirmation.
- Writes, network, remote installs, Git commits, and publishing require confirmation
  regardless of provenance.
- Consumers should execute `resolved_command` and `resolved_args` directly without a
  shell, never concatenate them into an interpolated command string.

Project runbooks are repository-controlled input. Review changes to
`.maestro/skill-runbooks.json` like executable build configuration.

`scripts/sync-templates.ps1` is dry-run by default, requires a Git repository target,
preserves existing files unless `-Force` is explicit, and never deletes the target's
`.github` directory or unrelated files.

## Installation and removal

Both skills use staging and backup rename, with rollback of the bundle if either
copy fails. Existing non-directory destinations are rejected. Configuration is a versioned multi-project
registry written through a temporary file. Project removal selects the exact
registered project; home cleanup removes only Maestro-owned filenames and never
recursively deletes an arbitrary `MAESTRO_HOME`.

## Dependencies and releases

The npm runtime has two direct dependencies: Commander and Clack Prompts. Release
workflows must run the complete Python and Node test suites before publishing and
keep package versions aligned. `release-layout.mjs` is the exact reviewed inventory;
sync copies only those inputs and writes exact npm `files` entries. Archive verification
reads actual tar bytes, rejects unexpected paths, symlinks, common secret formats and
personal paths, and records SHA-512 integrity. Inspect generic prose manually too:
pattern scanning cannot prove that arbitrary business information is public.

GitHub Actions use version tags with read-only repository permissions and checkout
credentials disabled. Before a future workflow publication, maintainers should verify
and pin the action tags to immutable upstream commit SHAs; this local-only change does
not guess unverified hashes.

## Supported versions

Security fixes are applied to `main` and the latest npm release. Older releases may
not receive backports.

## Reporting a vulnerability

Do not open a public issue containing exploit details, secrets, or private paths.
Use a private GitHub Security Advisory for `rodovalhofs/maestro` and include:

- affected version or commit;
- operating system and command;
- minimal reproduction with secrets removed;
- expected impact and suggested mitigation, if known.

The target for an initial maintainer response is seven business days.
