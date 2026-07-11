---
name: maestro
description: >-
  Local-first skill router and meta-orchestrator. Use when the user invokes
  $maestro or /maestro, asks which installed skills fit a task, or wants an
  editable dependency graph for work spanning multiple specialist skills.
disable-model-invocation: true
---

# Maestro

Route work to installed skills. Search locally, propose a small dependency graph,
wait for approval, then execute the approved graph. Maestro coordinates work; the
selected specialist skills define how each node is performed.

## Invariants

1. Start local. Running `search`, `route`, `manifest`, and `doctor` uses no network.
2. Show an editable graph and obtain explicit approval before spawning subagents.
3. Limit the graph to 10 nodes. Fuse skills that serve the same role.
4. Give every subagent the absolute path of each selected `SKILL.md`.
5. Keep `$maestro` out of subagent prompts to prevent recursive orchestration.
6. Treat network access, installation, publishing, messages, and destructive actions
   as separate effects that require the user's explicit authorization.
7. Use Git or GitHub only when the task asks for repository delivery or the user
   approves that addition. Local code work does not imply a push, issue, or PR.

## Workflow

### 1. Check the local installation

Run this when the manifest is missing, stale, or a command fails:

```bash
npx maestro-skills doctor
npx maestro-skills manifest --project-root "<workspace-root>"
```

`doctor` is read-only and does not use the network.

### 2. Search installed skills

```bash
npx maestro-skills search "<user prompt>" --project-root "<workspace-root>" --json
```

Use `--domain` only as a hint when the task clearly belongs to one bucket. Do not
discard cross-domain candidates solely because of that hint.

Read these fields:

- `results`: ranked installed skills and their absolute paths.
- `routing`: P0-P3 priority, decision, and confidence policy.
- `discover`: local gap analysis and privacy metadata.
- `runbooks`: validated preflight metadata and validation errors.
- `catalog`: manifest version and active project overlay.

For a decomposed task, refine each node in one call:

```bash
npx maestro-skills route --task "<task 1>" --task "<task 2>" --json
```

### 3. Draft the dependency graph

Choose the smallest graph that covers the task:

- one dominant skill: one node;
- a pipeline: order nodes by real dependency;
- independent work: parallel nodes followed by a synthesis node;
- broad plugin work: prefer its router skill over many overlapping leaves.

Present:

```markdown
## Maestro - proposed graph

| # | Node | Skills | Depends on | Effect |
|---|------|--------|------------|--------|
| 1 | <role> | `<skill>` | - | read / write / network |

Paths:
- `<skill>`: `<absolute path>/SKILL.md`

Edit the graph or reply `ok` to execute it.
```

The graph is complete when every requested outcome belongs to a node, every edge is
necessary, and each external effect is visible.

### 4. Handle remote discovery as an opt-in branch

`discover.triggered: true` means the local catalog has a possible gap. It is not
permission to query a remote service.

Add a disabled `Remote discovery` node that shows:

- service: `skills.sh`;
- sanitized query from `discover.queries`;
- effect: `network`;
- local fallback from `discover.local_fallback`.

Ask for explicit network consent before running:

```bash
npx skills find "<sanitized query>"
```

After results arrive, show the repository and skill source for review. Installation
is a second decision: present the command, but let the user run or explicitly request
it. An allowlist records prior trust; it never grants execution permission.

```bash
npx skills add <owner/repo@skill> -g -a <agent>
```

After an approved installation, rebuild the manifest, search again, and present a
new graph for approval. Keep the local fallback when discovery is declined or fails.

### 5. Apply runbooks safely

Runbook merge order is bundled, user, then project. Read `skill-runbooks.md` when a
result contains `runbook` or `runbooks.errors` is non-empty.

- A bundled, required, `read_local` preflight may be enabled by default.
- A user/project preflight or any write, network, install, Git, or publish effect
  stays disabled until explicitly approved.
- Execute the structured `resolved_command` plus `resolved_args`; do not concatenate
  them into a shell string.
- Stop the dependent node when a required preflight fails. Report optional failures
  without blocking unrelated work.

### 6. Execute the approved graph

Execute dependencies first and parallelize only independent nodes. Give each
subagent this minimum context:

```text
Read and follow:
<absolute SKILL.md paths>

Task:
<node-specific task>

Inputs from dependencies:
<relevant outputs only>

Return:
<completion criterion for this node>
```

Pause when execution would introduce an effect that was absent from the approved
graph. Ask for authorization instead of expanding scope.

### 7. Synthesize

Report the approved nodes that ran, their concrete outcomes, validation results,
remaining risks, and the next useful action. Mention GitHub artifacts only when they
actually exist.

## Local artifacts

| Path | Purpose |
|------|---------|
| `~/.maestro/skills-manifest.json` | Global catalog plus provenance |
| `~/.maestro/config.json` | Versioned installation registry |
| `~/.maestro/maestro-exclude.txt` | Local search exclusions |
| `~/.maestro/skill-runbooks.user.json` | User runbook overrides |
| `<project>/.maestro/skill-runbooks.json` | Project runbook overrides |
| `~/.maestro/discover-allowlist.txt` | Reviewed remote repositories |

On Windows, prefer the npm CLI. The PowerShell adapter is:

```powershell
& "$env:USERPROFILE\.codex\skills\maestro\scripts\invoke.ps1" search "<prompt>" --json
```
