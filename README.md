# Maestro

[![CI](https://github.com/rodovalhofs/maestro/actions/workflows/ci.yml/badge.svg)](https://github.com/rodovalhofs/maestro/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Meta-orquestrador de **skills para Cursor**: descobre skills locais, monta um grafo de dependências editável e orienta subagentes — com busca híbrida rápida (BM25 + manifest), roteamento **P0–P3**, intents, tags, sinônimos e detecção de skills ausentes.

> Inspirado em ideias de [task-skill-router](https://github.com/wcqxgjy6d8-pixel/task-skill-router), implementado como motor **local e rápido** (sem re-scan do filesystem a cada busca).

## O que este repo contém

| Pasta | Conteúdo |
|-------|----------|
| `skills/maestro/` | Skill Cursor + scripts Python + `community.yaml` |
| `tests/` | Testes automatizados do motor de busca |
| `docs/` | Fluxo GitHub genérico reutilizável |
| `templates/` | Issue templates, PR template e workflows para copiar em outros projetos |

## Pré-requisitos

- **Python 3.12+** (mesma versão do CI)
- **Cursor** com skills em `~/.cursor/skills` e/ou `~/.agents/skills`
- **PyYAML** (opcional) — melhora leitura de `community.yaml`; sem ele, usa parser embutido

## Instalação

```powershell
# Windows
git clone https://github.com/rodovalhofs/maestro.git
Copy-Item -Recurse -Force skills\maestro $env:USERPROFILE\.cursor\skills\maestro
```

```bash
# macOS / Linux
git clone https://github.com/rodovalhofs/maestro.git
cp -r skills/maestro ~/.cursor/skills/maestro
```

Opcional — skills ignoradas na busca:

```bash
cp skills/maestro/maestro-exclude.example.txt ~/.cursor/maestro-exclude.txt
```

## Uso no Cursor

Invoque com `$maestro` ou `/maestro` + sua tarefa.

### 1. Regenerar manifest (quando instalar novas skills)

Indexa `~/.cursor/skills`, `~/.agents/skills` e `.cursor/skills` do projeto:

```bash
py -3 ~/.cursor/skills/maestro/scripts/build_manifest.py --project-root /caminho/do/projeto
```

### 2. Buscar skills (prompt inteiro)

```bash
py -3 ~/.cursor/skills/maestro/scripts/search_skills.py "criar dashboard react" --json
```

Retorna `routing` (P0–P3), `confidence`, `mode`, `missing_skills`, `intent_boosts`.

### 3. Rotear sub-tarefas (após decompor o grafo)

```bash
printf '%s\n' "design UI" "fix CI" | py -3 ~/.cursor/skills/maestro/scripts/route_tasks.py --json
```

## Como funciona (resumo)

```text
Prompt do usuário
    → build_manifest.py (índice local, com tags)
    → search_skills.py (BM25 + sinônimos + intents + routing)
    → grafo editável (você confirma)
    → route_tasks.py por sub-tarefa (opcional)
    → subagentes com SKILL.md explícito
```

## Testes

```bash
python -m unittest discover -s tests -v
```

## Templates GitHub

Para copiar workflows e templates de Issue/PR para outro repositório:

```powershell
# Atenção: sobrescreve .github/ no destino
.\scripts\sync-templates.ps1 -TargetRepo "C:\caminho\do\seu\projeto"
```

Documentação: [docs/github-workflow.md](docs/github-workflow.md)

## Estrutura

```text
maestro/
├── .github/workflows/ci.yml
├── CONTRIBUTING.md
├── LICENSE
├── SECURITY.md
├── docs/github-workflow.md
├── scripts/sync-templates.ps1
├── skills/maestro/
│   ├── SKILL.md
│   ├── community.yaml
│   └── scripts/
├── tests/
└── templates/
```

## Contribuir

Veja [CONTRIBUTING.md](CONTRIBUTING.md). Issues e PRs são bem-vindos.

## Segurança

Veja [SECURITY.md](SECURITY.md). O Maestro só acessa arquivos locais de skills; não envia dados para servidores externos.

## Licença

[MIT](LICENSE) — Copyright (c) 2026 Yuri Rodovalho
