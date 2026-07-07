---
name: maestro
description: >-
  Meta-orchestrator that analyzes the user prompt, searches local skills via
  hybrid BM25 routing (intents, tags, synonyms, P0-P3), builds an editable
  dependency graph, and spawns focused subagents
  after user confirmation. Use when the user invokes $maestro, asks which skills
  to use, wants optimal skill routing, or has a complex task spanning multiple
  domains and does not know which skill to call.
disable-model-invocation: true
---

# Maestro

Orchestrate local Cursor skills. Maestro does **not** implement work itself — it discovers skills, plans a dependency graph, waits for user edits/approval, then spawns subagents.

## Hard rules

1. **Never spawn subagents before the user confirms the graph.**
2. **Max 10 graph nodes.** Fuse redundant skills that share the same role into one node.
3. **Pass explicit `SKILL.md` paths** to every subagent prompt.
4. **Do not invoke `$maestro` recursively** from subagents.
5. Routers like `index`, `data-visualization`, `grill-me`, `conselho` stay directly invocable — maestro may include them as hub nodes.
6. **Repos versionados:** aplicar o fluxo GitHub generico (Issues + PR + CI). Ver secao [GitHub workflow](#github-workflow) e `docs/github-workflow.md` neste repositorio.
7. **Discover seguro:** nunca executar `npx skills add` automaticamente; sem flag `-y`; install somente por acao humana apos revisar o repo.

## Artifacts

| File | Purpose |
|------|---------|
| `~/.maestro/skills-manifest.json` | Searchable catalog (regenerate with `manifest`) |
| `~/.maestro/maestro-exclude.txt` | Skills banned from search |
| `~/.maestro/skill-runbooks.user.json` | User runbook overrides |
| `~/.maestro/discover-allowlist.txt` | Optional trusted repos for Discover (install still manual) |
| `skill-runbooks.json` | Bundled runbooks (preflight CLI hints) |
| `scripts/build_manifest.py` | Regenerate manifest |
| `scripts/search_skills.py` | Hybrid BM25 search + routing + runbooks |
| `scripts/route_tasks.py` | Batch route decomposed sub-tasks |
| `scripts/invoke.ps1` / `invoke.sh` | Shell wrappers (PowerShell-safe) |

## Shell commands (read this first)

**Primary interface (all shells, including PowerShell):**

```bash
npx maestro-skills search "<user prompt>" --json
npx maestro-skills route --task "<task 1>" --task "<task 2>" --json
npx maestro-skills manifest --project-root "<workspace-root>"
npx maestro-skills runbook list
npx maestro-skills runbook add <skill> --summary "..." --notes "..."
```

**PowerShell fallback** (never use `%USERPROFILE%` — it does not expand in PowerShell):

```powershell
& "$env:USERPROFILE\.cursor\skills\maestro\scripts\invoke.ps1" search "<user prompt>" --json
```

**Unix:**

```bash
~/.cursor/skills/maestro/scripts/invoke.sh search "<user prompt>" --json
```

## Workflow

### 1. Refresh manifest (if stale or missing)

```bash
npx maestro-skills manifest --project-root "<workspace-root>"
```

Legacy: `invoke.ps1 manifest` or `python3 .../build_manifest.py --project-root "<workspace-root>"`

### 2. Search skills

```bash
npx maestro-skills search "<user prompt>" --json
```

Optional: `--domain web|data-viz|analytics|design|creative|devops-git|video-media|integrations|security|meta|general`

JSON includes `routing`, `confidence`, `mode`, `discover`, `runbooks`, and per-result `runbook` when defined.

Read `discover` before building the graph:

| `discover.triggered` | Meaning |
|----------------------|---------|
| `true` | Open a **Discover** branch via `find-skills` (see below) |
| `false` | Proceed with installed skills only |

**Discover reasons:** `force_discover` (explicit “find skill”), `weak_match`, `single_local_skill`, `concept_gap` (e.g. prompt mentions `skeleton-loader` with no local skill).

Follow `routing.priority` and `routing.decision`; use `results` as evidence.

### 2a. Discover branch (`discover.triggered: true`)

When the JSON signals discover, run **before presenting Graph 1**:

```bash
npx skills find "<query from discover.queries[0]>"
```

Repeat for each entry in `discover.queries` (max 2 concept gaps; extra gaps appear in `discover.gap_notes` as graph notes).

**Graph 1 — pré-discover** (wait for user **ok**):

| # | Nó | Skills | Depende de | Subagente |
|---|-----|--------|------------|-----------|
| 1 | Discover `<gap>` | `find-skills` | — | generalPurpose |
| | → candidata: `owner/repo@skill` (installs) | | | |
| 2 | Fallback local | `<discover.local_fallback>` | 1 (se discover falhar) | generalPurpose |
| 3 | Executar tarefa | `<instalada ou #2>` | 1 ou 2 | generalPurpose |

After user confirms Graph 1, **do not auto-install**. Present the install command for human review:

```bash
npx skills add <owner/repo@skill> -g -a cursor
```

Only if the user explicitly runs that command (or allowlists the repo in `~/.maestro/discover-allowlist.txt` and confirms), rebuild manifest:

```bash
npx maestro-skills manifest --project-root "<workspace-root>"
```

**Security:** Never pass `-y`. Never run `npx skills add` without explicit human action. See `SECURITY.md` and [skills.sh audits](https://www.skills.sh/rodovalhofs/maestro/maestro/security/agent-trust-hub).

Re-run search with the original prompt. Present **Graph 2 — pós-discover** and wait for a **second ok** before execution subagents.

**If `npx skills find` returns nothing:** Graph 2 uses `discover.local_fallback` only + note about `npx skills init`. If no fallback either, stop and ask the user how to proceed.

**If match is strong and `discover.triggered: false`:** skip Discover; single graph as usual.

### 2b. Refine graph nodes (after draft decomposition)

```bash
npx maestro-skills route --task "<task 1>" --task "<task 2>" --json
```

Merge router output into the graph: prefer installed `path` when `mode` is `auto-load`; honor `discover` flags from each task.

### 2c. Skill runbooks and preflight

Read `skill-runbooks.md`. When a search result includes `runbook.preflight`:

1. Add a **Preflight** node before the implementation node.
2. **Parent (Maestro) runs** the preflight CLI and attaches stdout to the subagent prompt.
3. If preflight fails, stop — do not spawn the implementation subagent.

Merge order: bundled `skill-runbooks.json` → `~/.maestro/skill-runbooks.user.json` → `<project>/.maestro/skill-runbooks.json`.

Users add custom runbooks:

```bash
npx maestro-skills runbook add my-skill --summary "..." --notes "..."
```

Para tarefas com codigo versionado, inclua no grafo nos de implementacao, git e sintese:

```bash
npx maestro-skills search "github issues PR yeet branch feat CI" --domain devops-git --json
```

Leia `docs/github-workflow.md` (neste repo ou copiado para o projeto) quando a tarefa tocar codigo versionado.

### 3. Handle weak matches

If `weak_match: true` and `discover.triggered: true`, prefer the **Discover branch** (step 2a) instead of only asking domain.

If `weak_match: true` and `discover.triggered: false`:

- **`low_top_score` / `tight_spread` / `no_results`** → ask domain in one line:

  > Domínio não ficou claro. Qual se aplica?
  > A) Web/apps  B) Data viz  C) Analytics  D) Design  E) Creative  F) Git/CI  G) Integrations  H) Security  I) Outro

  Re-run search with `--domain <choice>`.

- If prompt involves **codebase/repo** and match is still weak → run one `explore` subagent (`readonly: true`, `model: fast`) to gather context, append findings to query, search again.

### 4. Build dependency graph

From top search results (3–5 skills), design a **DAG**:

- **Single dominant skill** (score clearly ahead) → 1 node graph.
- **Pipeline** → order by dependency (research before build, build before QA).
- **Parallel** → only independent branches (e.g. `research` + `audit`), then merge.
- **Hub routers** → use `index` or `data-visualization` as one node instead of many leaf skills when the task is broad within that plugin.

**Fusion:** combine skills with the same role into one node. When `runbook.preflight` exists, split into `Preflight <id>` → `Implement` nodes:

```text
Node 2a — Preflight design-system [ui-ux-pro-max]
  run preflight CLI; attach output to Node 2b prompt
Node 2b — Implement UI [ui-ux-pro-max]
  skills: ui-ux-pro-max
  path: .../ui-ux-pro-max/SKILL.md
```

### 5. Present editable graph (mandatory)

Show this template and **wait for user edits or confirmation**:

```markdown
## Maestro — grafo proposto

**Prompt:** <one line>
**Domínio:** <domain_label>

| # | Nó | Skills | Depende de | Subagente |
|---|-----|--------|------------|-----------|
| 1 | <role> | `skill-a` | — | explore / generalPurpose |
| 2 | <role> | `skill-b`, `skill-c` | 1 | generalPurpose |

**Paths:**
- `skill-a`: C:/Users/.../.cursor/skills/skill-a/SKILL.md

Edite ordem, skills ou nós. Responda **ok** para executar ou descreva mudanças.
```

If graph would exceed 10 nodes: fuse, drop lowest-score leaves, or ask user which to cut.

### 6. Spawn subagents (after user OK)

Execute graph in dependency order. Parallelize independent nodes in one message.

**Subagent type map:**

| Task | `subagent_type` | Notes |
|------|-----------------|-------|
| Codebase discovery | `explore` | `readonly: true` |
| Implementation / analysis with skill | `generalPurpose` | Include full skill path + user task |
| Git / CI / shell ops | `shell` | Only when skill is git/ci focused |
| Read-only code review | `generalPurpose` | `readonly: true` |

**Subagent prompt template:**

```text
Read and follow this skill before acting:
<absolute-path-to-SKILL.md>

If multiple skills listed, read all paths and synthesize guidance.

User task:
<original user prompt + node-specific slice>

Prior node outputs:
<summary if any>

Return: concise result for maestro synthesis.
```

### 7. Synthesize

After all nodes complete, maestro (parent) delivers:

- What ran (nodes + skills)
- Key outcomes per node
- Recommended next step for the user
- **GitHub (se aplicavel):** Issue `#N`, branch `feat/N-slug`, PR URL, status CI

## GitHub workflow

Fluxo padrao para qualquer repositorio versionado:

| Regra | Valor |
|-------|--------|
| Branch | `feat/<N>-slug` ou `fix/<N>-slug` — nunca push direto na branch principal |
| Entrega | Issue → branch → testes locais → build → PR → CI verde → merge |
| CI | Job **test** antes de **build**; falha abre Issue com label `ci:falha` |
| Skills | `github`, `yeet`, `gh-fix-ci` nos nos git/publicacao/CI |
| Docs | `docs/github-workflow.md` e `templates/` neste repositorio |
| Agentes | Commits com `Refs #N` / `Closes #N`; informar PR URL ao encerrar |

**Fusion no grafo:** tarefas com implementacao + git viram pipeline `implementacao` → `yeet` (branch + PR draft), salvo tarefa so de leitura.

**Aplicar templates em um projeto:**

```bash
# Copie manualmente ou adapte o script sync-templates.ps1
cp -r templates/.github <seu-projeto>/
cp templates/CONTRIBUTING.md <seu-projeto>/
```

## Domain buckets

`web`, `data-viz`, `analytics`, `design`, `creative`, `devops-git`, `video-media`, `integrations`, `security`, `meta`, `general`

## Hub skills (prefer as single node when broad)

- `index` — Product Design plugin router
- `data-visualization` / `build-web-data-visualization-data-visualization` — viz router

## Examples

**User:** `$maestro vamos colocar skeleton-loader na UI`

1. Search → `discover.triggered` (`concept_gap: skeleton-loader`); local UI skills as fallback
2. `npx skills find "skeleton-loader ui web"` → candidata no Grafo 1
3. User ok → find-skills installs → rebuild manifest → Grafo 2 → user ok → implement

**User:** `$maestro corrigir CI quebrado no PR`

1. Search → `gh-fix-ci`, `github`
2. Graph: 1 node → `gh-fix-ci` (+ regra GitHub: branch `feat/N`, PR, nao main)
3. User confirms → spawn `shell` or `generalPurpose` subagent with skill path

**User:** `$maestro criar dashboard de vendas com React`

1. Search domain `web` + `data-viz` → may need domain question
2. Graph: `data-visualization` → `react-and-nextjs-data-visualization` → `dashboards-and-real-time-visualization`
3. User edits → confirm → sequential subagents

## Maintenance

After syncing skills or editing runbooks:

```bash
npx maestro-skills manifest
```

After changing this repo, run `node scripts/sync-skill-to-cli.mjs` before npm publish (maintainer only).
