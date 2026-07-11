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

`discover.triggered` reports a possible catalog gap; it does not perform a request.
The agent must show the target service and sanitized query, then obtain explicit
network consent before using `npx skills find`.

Remote skill installation is a separate decision. Review the repository, its
`SKILL.md`, scripts, dependencies, and maintainer identity before running a displayed
`npx skills add` command. Maestro does not auto-install and does not add `-y`.
`discover-allowlist.txt` records trust context only; it is never execution permission.

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

Skill replacement uses a staging directory and backup rename so a failed copy can
restore the previous installation. Configuration is a versioned multi-project
registry written through a temporary file. Project removal selects the exact
registered project; home cleanup removes only Maestro-owned filenames and never
recursively deletes an arbitrary `MAESTRO_HOME`.

## Dependencies and releases

The npm runtime has two direct dependencies: Commander and Clack Prompts. Release
workflows must run the complete Python and Node test suites before publishing. Inspect
the output of `npm pack --dry-run` for both packages and keep package versions aligned.

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
