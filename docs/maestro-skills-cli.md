# CLI `maestro-skills`

Instalação interativa do Maestro para vários agentes de IA.

## Comando principal

```bash
npx maestro-skills setup
```

Pacote npm: [maestro-skills@0.1.2](https://www.npmjs.com/package/maestro-skills)

Alternativa scoped (bin `maestro`):

```bash
npx @rodovalhofs/maestro setup
```

## O que o setup faz

1. Detecta agentes no sistema
2. Você escolhe destinos (multi-select)
3. Escolhe escopo: **global** (padrão) ou **este projeto** (`--project`)
4. Copia a skill `maestro/` para cada pasta de skills
5. Opcional: registra no [skills.sh](https://skills.sh/) via `npx skills add`
6. Migra manifest legado `~/.cursor/skills-manifest.json` → `~/.maestro/`
7. Executa `build_manifest.py` (Python 3.12+)

## Agentes suportados

| ID | Agente | Pasta global | CLI flag |
|----|--------|--------------|----------|
| `cursor` | Cursor | `~/.cursor/skills/maestro` | `--cursor` |
| `claude` | Claude Code | `~/.claude/skills/maestro` | `--claude` |
| `codex` | Codex | `~/.codex/skills/maestro` | `--codex` |
| `universal` | Universal | `~/.agents/skills/maestro` | `--universal` |

Novos agentes: edite `packages/maestro-skills/agents.json`.

## Comandos

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
└── config.json
```

O `build_manifest.py` indexa skills de `~/.cursor`, `~/.claude`, `~/.codex`, `~/.agents` e pastas de projeto.

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

```bash
npm login
npm run publish:cli
npm run publish:scoped
```

Ou workflow **Publish npm** com secret `NPM_TOKEN`.
