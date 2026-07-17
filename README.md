<div align="center">

# Maestro

**Meta-orquestrador de skills para agentes de IA**

Descubra skills locais, monte um grafo editável e execute com subagentes —  
sem adivinhar qual skill chamar.

<br>

[![CI](https://github.com/rodovalhofs/maestro/actions/workflows/ci.yml/badge.svg)](https://github.com/rodovalhofs/maestro/actions/workflows/ci.yml)
[![npm](https://img.shields.io/npm/v/maestro-skills?label=maestro-skills)](https://www.npmjs.com/package/maestro-skills)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Node](https://img.shields.io/badge/node-%3E%3D18-brightgreen)](package.json)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](.github/workflows/ci.yml)
[![Socket Badge](https://badge.socket.dev/npm/package/maestro-skills/0.1.3)](https://badge.socket.dev/npm/package/maestro-skills/0.1.3)

<br>

```bash
npx maestro-skills setup
```

[Documentação do CLI](docs/maestro-skills-cli.md) · [skills.sh](https://skills.sh/rodovalhofs/maestro) · [Issues](https://github.com/rodovalhofs/maestro/issues)

</div>

<br>

---

## Visão geral

O **Maestro** responde à pergunta:

> *Para esta tarefa, quais skills devo usar, em que ordem, e preciso instalar algo novo?*

Ele **não implementa** o trabalho — orquestra: busca skills instaladas, propõe um **grafo de dependências**, espera sua confirmação e só então dispara subagentes com os `SKILL.md` corretos.

| | |
|---|---|
| **Agentes** | Cursor · Claude Code · Codex · Universal (`~/.agents/skills`) |
| **Motor** | BM25 normalizado + boost limitado de nome/tags + manifest local (`~/.maestro/`) |
| **Discover** | Detecta lacunas (`skeleton-loader`, libs no prompt) e busca no [skills.sh](https://skills.sh/) |
| **Roteamento** | Prioridade P0–P3 · intents · concept gaps · sinônimos PT/EN |

> Inspirado em ideias de [task-skill-router](https://github.com/wcqxgjy6d8-pixel/task-skill-router).

---

## Início rápido

### 1. Instalar (interativo)

```bash
npx maestro-skills setup
```

O setup detecta agentes, pergunta onde instalar (global ou `--project`), copia a skill e gera o manifest.

| Agente | Pasta | Flag |
|--------|-------|------|
| Cursor | `~/.cursor/skills/maestro` | `--cursor` |
| Claude Code | `~/.claude/skills/maestro` | `--claude` |
| Codex | `~/.codex/skills/maestro` | `--codex` |
| Universal | `~/.agents/skills/maestro` | `--universal` |

```bash
# Exemplos
npx maestro-skills setup --codex --cursor -y
npx maestro-skills setup --project
npx @rodovalhofs/maestro setup          # bin curto (scoped)
```

### 2. Usar no agente

```text
$maestro criar dashboard de vendas com React
$maestro vamos colocar skeleton-loader na UI
$maestro corrigir CI quebrado no PR #42
```

### 3. Regenerar índice (após instalar novas skills)

```bash
py -3 ~/.cursor/skills/maestro/scripts/build_manifest.py --project-root .
```

Manifest: `~/.maestro/skills-manifest.json`

---

## Como funciona

```text
  Seu prompt
      │
      ▼
  search_skills.py ──► match forte? ──► grafo único → ok → subagentes
      │
      └─ discover.triggered
              │
              ▼
          npx skills find → Grafo 1 → ok → install → Grafo 2 → ok → execução
```

### Gatilhos do ramo Discover

| Sinal | Exemplo |
|-------|---------|
| `weak_match` | Nenhuma skill local confiável |
| `concept_gap` | *"colocar skeleton-loader na UI"* |
| `force_discover` | *"find a skill for changelog"* |
| `single_local_skill` | Um candidato local com score baixo |

Máximo de **2** concept gaps por prompt.

---

## O que faz / o que não faz

| Faz | Não faz |
|-----|---------|
| Busca skills **instaladas** e monta grafo | Implementar código sozinho |
| Detecta conceitos sem skill local | Spawnar subagentes sem seu **ok** |
| Sugere install via `npx skills find` | Enviar dados para servidores externos |
| Roteia P0–P3 com confirmação em alto risco | Substituir o agente principal |

---

## Outras formas de instalar

<details>
<summary><strong>npx skills</strong> (catálogo skills.sh)</summary>

```bash
npx skills add rodovalhofs/maestro --skill maestro -g -a cursor -a codex -y
```

</details>

<details>
<summary><strong>Git clone</strong> (manual)</summary>

```powershell
git clone https://github.com/rodovalhofs/maestro.git
Copy-Item -Recurse -Force maestro\skills\maestro $env:USERPROFILE\.codex\skills\maestro
```

```bash
git clone https://github.com/rodovalhofs/maestro.git
cp -r maestro/skills/maestro ~/.codex/skills/maestro
```

Depois rode `build_manifest.py` (ver acima).

</details>

---

## CLI de debug

```bash
# Buscar skills (recomendado — funciona no PowerShell)
npx maestro-skills search "dashboard react" --json

# Rotear sub-tarefas
npx maestro-skills route --task "design UI" --task "fix CI" --json

# Regenerar manifest
npx maestro-skills manifest --project-root .

# Runbooks do usuário
npx maestro-skills runbook list
npx maestro-skills runbook init-allowlist
```

PowerShell fallback: `& "$env:USERPROFILE\.cursor\skills\maestro\scripts\invoke.ps1" search "..." --json`

Campos úteis no JSON: `results`, `routing`, `discover`, `runbook` (por skill), `weak_match`, `metadata_boost` e `metadata_matches`.

A busca normaliza maiúsculas e diacríticos, portanto consultas como `código` e `codigo` são equivalentes. Correspondências completas de nomes e tags compostas recebem um boost limitado por skill; tags repetidas não acumulam score.

Domínios (`--domain`): `web` · `data-viz` · `analytics` · `design` · `creative` · `devops-git` · `video-media` · `integrations` · `security` · `meta` · `general`

---

## Repositório

```text
maestro/
├── packages/maestro-skills/   ← CLI npm (npx maestro-skills)
├── skills/maestro/            ← skill + scripts Python
├── tests/                     ← motor de busca
├── docs/                      ← CLI + fluxo GitHub
└── templates/                 ← Issue/PR para outros repos
```

| Pasta | Conteúdo |
|-------|----------|
| `skills/maestro/` | `SKILL.md`, `search_skills.py`, `concept_gaps.py`, … |
| `packages/maestro-skills/` | `setup` / `remove` interativos |
| `docs/` | [maestro-skills-cli.md](docs/maestro-skills-cli.md) · [github-workflow.md](docs/github-workflow.md) |

---

## Pré-requisitos

| Ferramenta | Necessário | Para quê |
|------------|------------|----------|
| **Node.js 18+** | Setup / Discover | `npx maestro-skills`, `npx skills find` |
| **Python 3.12+** | Busca / manifest | `search_skills.py`, `build_manifest.py` |
| **Agente com skills** | Uso | Cursor, Claude, Codex ou `~/.agents/skills` |

---

## Desenvolvimento

```bash
py -3 -m unittest discover -s tests -v
cd packages/maestro-skills && npm test
```

---

## Contribuir · Segurança · Licença

- [CONTRIBUTING.md](CONTRIBUTING.md) — Issues e PRs bem-vindos
- [SECURITY.md](SECURITY.md) — revise pacotes de `npx skills find` antes de instalar
- [MIT](LICENSE) — Copyright (c) 2026 Yuri Rodovalho
