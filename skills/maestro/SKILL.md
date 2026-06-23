---
name: maestro
description: >-
  Meta-orchestrator that analyzes the user prompt, searches ~500+ local skills
  via BM25, builds an editable dependency graph, and spawns focused subagents
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

## Artifacts

| File | Purpose |
|------|---------|
| `~/.cursor/skills-manifest.json` | Searchable catalog (regenerate with build-manifest) |
| `~/.cursor/maestro-exclude.txt` | Skills banned from search |
| `scripts/build-manifest.py` | Regenerate manifest |
| `scripts/search-skills.py` | BM25 search by domain bucket |

## Workflow

### 1. Refresh manifest (if stale or missing)

```bash
py -3 "%USERPROFILE%\.cursor\skills\maestro\scripts\build-manifest.py" --project-root "<workspace-root>"
```

Fallback: `python` instead of `py -3` if needed.

On Unix: `python3 ~/.cursor/skills/maestro/scripts/build-manifest.py --project-root "<workspace-root>"`

### 2. Search skills

```bash
py -3 "%USERPROFILE%\.cursor\skills\maestro\scripts\search-skills.py" "<user prompt>" --json
```

Optional: `--domain web|data-viz|analytics|design|creative|devops-git|video-media|integrations|meta|general`

Para tarefas com codigo versionado, inclua no grafo nos de implementacao, git e sintese:

```bash
py -3 "%USERPROFILE%\.cursor\skills\maestro\scripts\search-skills.py" "github issues PR yeet branch feat CI" --domain devops-git --json
```

Leia `docs/github-workflow.md` (neste repo ou copiado para o projeto) quando a tarefa tocar codigo versionado.

### 3. Handle weak matches

If `weak_match: true` in JSON:

- **`low_top_score` / `tight_spread` / `no_results`** → ask domain in one line:

  > Domínio não ficou claro. Qual se aplica?
  > A) Web/apps  B) Data viz  C) Analytics  D) Design  E) Creative  F) Git/CI  G) Integrations  H) Outro

  Re-run search with `--domain <choice>`.

- If prompt involves **codebase/repo** and match is still weak → run one `explore` subagent (`readonly: true`, `model: fast`) to gather context, append findings to query, search again.

### 4. Build dependency graph

From top search results (3–5 skills), design a **DAG**:

- **Single dominant skill** (score clearly ahead) → 1 node graph.
- **Pipeline** → order by dependency (research before build, build before QA).
- **Parallel** → only independent branches (e.g. `research` + `audit`), then merge.
- **Hub routers** → use `index` or `data-visualization` as one node instead of many leaf skills when the task is broad within that plugin.

**Fusion:** combine skills with the same role into one node:

```text
Node 2 — Implement UI [react-best-practices + shadcn-best-practices]
  skills: react-best-practices, shadcn-best-practices
  path: .../react-best-practices/SKILL.md (read all listed skills)
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

`web`, `data-viz`, `analytics`, `design`, `creative`, `devops-git`, `video-media`, `integrations`, `meta`, `general`

## Hub skills (prefer as single node when broad)

- `index` — Product Design plugin router
- `data-visualization` / `build-web-data-visualization-data-visualization` — viz router

## Examples

**User:** `$maestro corrigir CI quebrado no PR`

1. Search → `gh-fix-ci`, `github`
2. Graph: 1 node → `gh-fix-ci` (+ regra GitHub: branch `feat/N`, PR, nao main)
3. User confirms → spawn `shell` or `generalPurpose` subagent with skill path

**User:** `$maestro criar dashboard de vendas com React`

1. Search domain `web` + `data-viz` → may need domain question
2. Graph: `data-visualization` → `react-and-nextjs-data-visualization` → `dashboards-and-real-time-visualization`
3. User edits → confirm → sequential subagents

## Maintenance

After syncing Codex skills, regenerate manifest:

```bash
py -3 ~/.cursor/skills/maestro/scripts/build-manifest.py
```

Or run the full sync script which rebuilds manifest automatically.
