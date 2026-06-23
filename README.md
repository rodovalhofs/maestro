# Maestro

Meta-orquestrador de skills para Cursor: busca BM25 em centenas de skills locais, monta grafo de dependencias e dispara subagentes apos confirmacao do usuario.

Este repositorio contem:

- `skills/maestro/` — skill e scripts (`build-manifest.py`, `search-skills.py`)
- `docs/github-workflow.md` — fluxo generico Issue → PR → CI (reutilizavel em qualquer repo)
- `templates/` — CONTRIBUTING, PR template, issue templates e workflows GitHub Actions

## Instalacao da skill

Copie a pasta da skill para o Cursor:

```powershell
# Windows
Copy-Item -Recurse skills\maestro $env:USERPROFILE\.cursor\skills\maestro
```

```bash
# macOS / Linux
cp -r skills/maestro ~/.cursor/skills/maestro
```

Opcional: copie `maestro-exclude.example.txt` para `~/.cursor/maestro-exclude.txt` e edite skills a ignorar na busca.

## Uso

No Cursor, invoque com `$maestro` ou `/maestro` seguido da tarefa.

### Regenerar manifest de skills

```bash
py -3 ~/.cursor/skills/maestro/scripts/build-manifest.py --project-root /caminho/do/projeto
```

### Buscar skills

```bash
py -3 ~/.cursor/skills/maestro/scripts/search-skills.py "criar dashboard react" --json
```

## Fluxo GitHub generico

Veja [docs/github-workflow.md](docs/github-workflow.md).

Para aplicar templates em outro projeto:

```powershell
.\scripts\sync-templates.ps1 -TargetRepo "C:\caminho\do\projeto"
```

## Estrutura

```text
maestro/
├── docs/github-workflow.md
├── scripts/sync-templates.ps1
├── skills/maestro/
│   ├── SKILL.md
│   ├── maestro-exclude.example.txt
│   └── scripts/
└── templates/
    ├── CONTRIBUTING.md
    ├── labels.json
    ├── pull_request_template.md
    └── .github/
```

## Licenca

Uso interno. Ajuste conforme necessario.
