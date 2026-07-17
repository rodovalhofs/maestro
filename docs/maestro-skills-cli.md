# CLI `maestro-skills`

Instalação interativa do Maestro para vários agentes de IA.

## Comando principal

```bash
npx maestro-skills setup
```

Pacote npm: [maestro-skills](https://www.npmjs.com/package/maestro-skills)

Alternativa scoped (bin `maestro`):

```bash
npx @rodovalhofs/maestro setup
```

## O que o setup faz

1. Detecta agentes no sistema
2. Você escolhe destinos (multi-select)
3. Escolhe escopo: **global** (padrão) ou **este projeto** (`--project`)
4. Copia a skill `maestro/` para cada pasta de skills
5. Opcional: registra no [skills.sh](https://skills.sh/) — **sem `-y` automático**; revisão manual
6. Migra manifest legado `~/.cursor/skills-manifest.json` → `~/.maestro/`
7. Executa `build_manifest.py` (Python 3.12+)

## Busca e roteamento (PowerShell-safe)

Use o CLI npm em vez de `%USERPROFILE%` (não expande no PowerShell):

```bash
npx maestro-skills search "dashboard react" --json
npx maestro-skills route --task "design UI" --task "fix CI" --json
npx maestro-skills manifest --project-root .
```

A busca trata consultas com e sem acentos como equivalentes. Nos resultados JSON, `metadata_boost` e `metadata_matches` explicam quando um nome, pasta ou tag completa desempatou o ranking; o boost usa apenas a melhor correspondência e não recompensa quantidade de tags.

PowerShell fallback:

```powershell
& "$env:USERPROFILE\.cursor\skills\maestro\scripts\invoke.ps1" search "..." --json
```

## Runbooks do usuário

```bash
npx maestro-skills runbook list
npx maestro-skills runbook add my-skill --summary "..." --notes "..."
npx maestro-skills runbook edit my-skill
npx maestro-skills runbook init-allowlist
```

Arquivos:

| Arquivo | Escopo |
|---------|--------|
| `skill-runbooks.json` (bundled) | Shipped com Maestro |
| `~/.maestro/skill-runbooks.user.json` | Global do usuário |
| `.maestro/skill-runbooks.json` | Por projeto (opcional) |

## Agentes suportados

| ID | Agente | Pasta global | CLI flag |
|----|--------|--------------|----------|
| `cursor` | Cursor | `~/.cursor/skills/maestro` | `--cursor` |
| `claude` | Claude Code | `~/.claude/skills/maestro` | `--claude` |
| `codex` | Codex | `~/.codex/skills/maestro` | `--codex` |
| `universal` | Universal | `~/.agents/skills/maestro` | `--universal` |

Novos agentes: edite `packages/maestro-skills/agents.json`.

## Comandos setup/remove

```bash
npx maestro-skills setup
npx maestro-skills setup --codex --cursor -y
npx maestro-skills setup --project
npx maestro-skills remove
npx maestro-skills remove -y --clean-home
```

## Layout `~/.maestro/`

```text
~/.maestro/
├── skills-manifest.json
├── maestro-exclude.txt
├── skill-runbooks.user.json
├── discover-allowlist.txt
└── config.json
```

O `build_manifest.py` indexa skills de `~/.cursor`, `~/.claude`, `~/.codex`, `~/.agents` e pastas de projeto. Veja [SECURITY.md](../SECURITY.md) para escopo de leitura local.

## Pré-requisitos

- **Node.js 18+** — CLI
- **Python 3.12+** — manifest (`py -3` ou `python3`)

## Desenvolvimento

```bash
node scripts/sync-skill-to-cli.mjs
py -3 -m unittest discover -s tests -v
cd packages/maestro-skills && npm test
```

## Publicação npm (mantenedores)

Somente o mantenedor executa publish localmente:

```bash
npm login
npm run publish:cli
npm run publish:scoped
```

Ou workflow **Publish npm** com secret `NPM_TOKEN`.
