# CLI `maestro-skills`

Instalação interativa do Maestro para vários agentes de IA — um comando, escolha onde instalar.

## Comando principal

**GitHub (funciona sem publicar no npm):**

```bash
npx github:rodovalhofs/maestro maestro-skills setup
```

**npm registry** (após `maestro-skills@0.1.1` publicado):

```bash
npx maestro-skills setup
```

Equivalente scoped (bin `maestro`):

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

Novos agentes podem ser adicionados em `packages/maestro-skills/agents.json` sem alterar o core do CLI.

## Comandos

```bash
# Setup interativo (recomendado)
npx maestro-skills setup

# Só Codex, global, sem prompts
npx maestro-skills setup --codex -y

# Vários agentes
npx maestro-skills setup --cursor --claude --codex -y

# Apenas o repositório atual
npx maestro-skills setup --project

# Desinstalar
npx maestro-skills remove
npx maestro-skills remove -y --clean-home
```

## Layout `~/.maestro/`

```text
~/.maestro/
├── skills-manifest.json   # índice único (todos os agentes)
├── maestro-exclude.txt    # skills ignoradas na busca
└── config.json            # último setup (destinos, escopo)
```

O `build_manifest.py` indexa skills de:

- `~/.cursor/skills`
- `~/.claude/skills`
- `~/.codex/skills`
- `~/.agents/skills`
- `.cursor/skills`, `.claude/skills`, `.codex/skills`, `.agents/skills` do `--project-root`

## Pré-requisitos

- **Node.js 18+** — para o CLI
- **Python 3.12+** — para gerar o manifest (`py -3` ou `python3`)

## Desenvolvimento

```bash
# Sincronizar skill canônica → pacotes npm
node scripts/sync-skill-to-cli.mjs

# Testes Python
py -3 -m unittest discover -s tests -v

# Testes Node
cd packages/maestro-skills && npm test
```

## Publicação npm

O pacote `maestro-skills` precisa ser publicado uma vez para `npx maestro-skills` funcionar sem GitHub.

```bash
npm login
npm run publish:cli    # maestro-skills
npm run publish:scoped # @rodovalhofs/maestro
```

Ou dispare o workflow **Publish npm** no GitHub Actions (secret `NPM_TOKEN`).

Não inclua tokens, `.env` ou credenciais nos pacotes.
