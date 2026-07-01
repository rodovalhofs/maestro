# Maestro

[![CI](https://github.com/rodovalhofs/maestro/actions/workflows/ci.yml/badge.svg)](https://github.com/rodovalhofs/maestro/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Maestro** é um meta-orquestrador de skills para o Cursor. Você descreve a tarefa; ele descobre quais skills locais usar, monta um **grafo de dependências editável**, pede sua confirmação e só então dispara subagentes com os `SKILL.md` certos.

Se faltar skill no ecossistema (ex.: `skeleton-loader`), o Maestro abre o ramo **Discover** via [find-skills](https://skills.sh/) (`npx skills find`), instala, regenera o índice e roteia de novo.

> Motor **local e rápido** (BM25 + manifest JSON) — sem re-scan do filesystem a cada busca.  
> Inspirado em ideias de [task-skill-router](https://github.com/wcqxgjy6d8-pixel/task-skill-router).

---

## O que o Maestro faz (e o que não faz)

| Faz | Não faz |
|-----|---------|
| Analisa seu prompt e busca skills **já instaladas** | Implementar código por conta própria |
| Monta um grafo de nós (pesquisa → implementação → CI…) | Spawnar subagentes sem você confirmar o grafo |
| Detecta **lacunas de conceito** (`skeleton-loader`, libs citadas no prompt) | Substituir o agente principal do Cursor |
| Sugere instalar skills via `npx skills find` quando necessário | Enviar dados para servidores externos |
| Roteia com prioridade **P0–P3** (auto-load vs recomendar) | Ignorar tarefas de alto risco (deploy, secrets) sem confirmação |

### Em uma frase

O Maestro responde: *“Para esta tarefa, quais skills devo usar, em que ordem, e preciso instalar algo novo?”*

---

## Fluxo completo

```text
Seu prompt
    │
    ▼
build_manifest.py          ← índice local (~/.cursor/skills-manifest.json)
    │
    ▼
search_skills.py             ← BM25 + intents + sinônimos + concept gaps
    │
    ├─ match forte, sem lacunas
    │       └─► Grafo único → você confirma → subagentes executam
    │
    └─ discover.triggered
            │
            ▼
        npx skills find      ← pré-busca no ecossistema (skills.sh)
            │
            ▼
        Grafo 1 (Discover + fallback local) → você: ok
            │
            ▼
        find-skills install + build_manifest.py
            │
            ▼
        Grafo 2 (execução) → você: ok
            │
            ▼
        subagentes com SKILL.md explícito → síntese final
```

### Quando o ramo Discover abre

| Sinal | Exemplo |
|-------|---------|
| `weak_match` | Nenhuma skill local confiável para o prompt |
| `concept_gap` | *“colocar skeleton-loader na UI”* — termo sem skill local |
| `force_discover` | *“find a skill for changelog”*, `npx skills find` |
| `single_local_skill` | Só um candidato local e score baixo |

Máximo de **2** gaps por prompt; extras viram nota no grafo para você editar.

---

## Instalação

### Opção A — `npx skills` (recomendado)

Requer [Node.js](https://nodejs.org/). Instala a skill no Cursor globalmente:

```bash
npx skills add rodovalhofs/maestro --skill maestro -g -a cursor -y
```

| Flag | Significado |
|------|-------------|
| `--skill maestro` | Só a skill Maestro (o repo tem uma) |
| `-g` | Global (`~/.cursor/skills`) |
| `-a cursor` | Destino: Cursor |
| `-y` | Sem prompts interativos |

**Windows (PowerShell):**

```powershell
npx skills add rodovalhofs/maestro --skill maestro -g -a cursor -y
```

**Verificar instalação:**

```bash
npx skills list
```

**Catálogo público:** após installs, a skill pode aparecer em [skills.sh/rodovalhofs/maestro](https://skills.sh/rodovalhofs/maestro).

### Opção B — Git clone (manual)

```powershell
# Windows
git clone https://github.com/rodovalhofs/maestro.git
Copy-Item -Recurse -Force maestro\skills\maestro $env:USERPROFILE\.cursor\skills\maestro
```

```bash
# macOS / Linux
git clone https://github.com/rodovalhofs/maestro.git
cp -r maestro/skills/maestro ~/.cursor/skills/maestro
```

### Pós-instalação (obrigatório)

Indexe suas skills locais para o Maestro poder buscar:

```bash
# Windows
py -3 %USERPROFILE%\.cursor\skills\maestro\scripts\build_manifest.py --project-root .

# macOS / Linux
python3 ~/.cursor/skills/maestro/scripts/build_manifest.py --project-root .
```

Rode de novo sempre que instalar ou remover skills.

### Opcional — excluir skills da busca

```bash
cp ~/.cursor/skills/maestro/maestro-exclude.example.txt ~/.cursor/maestro-exclude.txt
# edite o arquivo e regenere o manifest
```

---

## Pré-requisitos

| Ferramenta | Obrigatório | Uso |
|------------|-------------|-----|
| **Cursor** | Sim | Agent skills em `~/.cursor/skills` e/ou `~/.agents/skills` |
| **Python 3.12+** | Sim | Scripts de busca e manifest (mesma versão do CI) |
| **Node.js** | Para Discover | `npx skills find` / `npx skills add` no ramo find-skills |

---

## Uso no Cursor

Invoque com **`$maestro`** ou **`/maestro`** + sua tarefa:

```text
$maestro criar dashboard de vendas com React e gráficos
$maestro vamos colocar skeleton-loader na tela de produtos
$maestro corrigir CI quebrado no PR #42
```

O agente segue o `SKILL.md` do Maestro: busca → grafo editável → confirmação → execução.

### Ferramentas CLI (uso direto ou debug)

**1. Regenerar manifest**

```bash
py -3 ~/.cursor/skills/maestro/scripts/build_manifest.py --project-root /caminho/do/projeto
```

**2. Buscar skills para um prompt**

```bash
py -3 ~/.cursor/skills/maestro/scripts/search_skills.py "criar dashboard react" --json
```

Campos úteis no JSON:

| Campo | Significado |
|-------|-------------|
| `results` | Skills locais ranqueadas (score, confidence, path) |
| `routing` | `P0`–`P3` e decisão (`auto-load`, `recommend`, `bypass`) |
| `discover` | `triggered`, `reasons`, `gaps`, `queries`, `local_fallback` |
| `weak_match` | Match local fraco — pode pedir domínio ou Discover |

**3. Rotear sub-tarefas (grafo decomposto)**

```bash
printf '%s\n' "design UI" "fix CI" | py -3 ~/.cursor/skills/maestro/scripts/route_tasks.py --json
```

**Domínios** (`--domain`): `web`, `data-viz`, `analytics`, `design`, `creative`, `devops-git`, `video-media`, `integrations`, `security`, `meta`, `general`.

---

## Exemplos de comportamento

### Tarefa com skill local clara

```text
Prompt: corrigir CI quebrado no PR
→ discover.triggered: false
→ top: gh-fix-ci, github
→ Grafo: 1 nó → você confirma → subagente executa
```

### Conceito sem skill local

```text
Prompt: vamos colocar skeleton-loader na UI
→ discover.triggered: true (concept_gap: skeleton-loader)
→ npx skills find "skeleton-loader ui web"
→ Grafo 1 com Discover → install → Grafo 2 → implementação
```

### Descoberta explícita

```text
Prompt: find a skill for changelog
→ discover.triggered: true (force_discover)
→ find-skills busca no skills.sh
```

---

## O que há neste repositório

| Pasta | Conteúdo |
|-------|----------|
| `skills/maestro/` | Skill Cursor + scripts Python (`search_skills`, `concept_gaps`, …) |
| `tests/` | 18+ testes do motor de busca |
| `docs/` | Fluxo GitHub genérico (Issues + PR + CI) |
| `templates/` | Issue templates, PR template e workflows para copiar em outros projetos |

```text
maestro/
├── .github/workflows/ci.yml
├── skills/maestro/
│   ├── SKILL.md              ← regras do orquestrador
│   ├── maestro-exclude.example.txt
│   └── scripts/
│       ├── build_manifest.py
│       ├── search_skills.py
│       ├── concept_gaps.py
│       ├── route_tasks.py
│       └── …
├── tests/
├── docs/github-workflow.md
└── templates/
```

---

## Testes

```bash
py -3 -m unittest discover -s tests -v
```

---

## Templates GitHub

Copie workflows e templates de Issue/PR para outro repositório:

```powershell
# Atenção: sobrescreve .github/ no destino
.\scripts\sync-templates.ps1 -TargetRepo "C:\caminho\do\seu\projeto"
```

Detalhes: [docs/github-workflow.md](docs/github-workflow.md)

---

## Contribuir

Veja [CONTRIBUTING.md](CONTRIBUTING.md). Issues e PRs são bem-vindos.

## Segurança

Veja [SECURITY.md](SECURITY.md). O Maestro lê apenas pastas locais de skills; revise pacotes de `npx skills find` antes de instalar.

## Licença

[MIT](LICENSE) — Copyright (c) 2026 Yuri Rodovalho
