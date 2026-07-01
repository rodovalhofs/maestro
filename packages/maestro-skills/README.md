# maestro-skills

CLI de instalação interativa do Maestro — estilo `npx ctx7 setup`.

## Instalação

```bash
npx maestro-skills setup
```

Fallback (bin curto `maestro`):

```bash
npx @rodovalhofs/maestro setup
```

## Agentes suportados (v1)

| Agente | Pasta global | Flag |
|--------|--------------|------|
| Cursor | `~/.cursor/skills` | `--cursor` |
| Claude Code | `~/.claude/skills` | `--claude` |
| Codex | `~/.codex/skills` | `--codex` |
| Universal | `~/.agents/skills` | `--universal` |

## Comandos

```bash
npx maestro-skills setup              # interativo
npx maestro-skills setup --codex -y   # só Codex, sem prompts
npx maestro-skills setup --project    # só o projeto atual
npx maestro-skills remove             # desinstalar
```

Índice de skills: `~/.maestro/skills-manifest.json`

Documentação completa: [docs/maestro-skills-cli.md](../../docs/maestro-skills-cli.md)
