# Maestro

Meta-orquestrador de skills para Cursor: busca hibrida BM25 (rapida, baseada em manifest) com roteamento P0-P3, intents, tags, sinonimos e deteccao de skills ausentes.

Este repositorio contem:

- `skills/maestro/` — skill, scripts e `community.yaml`
- `tests/` — testes automatizados do motor de busca
- `docs/github-workflow.md` — fluxo generico Issue → PR → CI
- `templates/` — CONTRIBUTING, PR template, issue templates e workflows GitHub Actions

## Instalacao da skill

```powershell
# Windows
Copy-Item -Recurse -Force skills\maestro $env:USERPROFILE\.cursor\skills\maestro
```

```bash
# macOS / Linux
cp -r skills/maestro ~/.cursor/skills/maestro
```

Opcional: copie `maestro-exclude.example.txt` para `~/.cursor/maestro-exclude.txt`.

## Uso

No Cursor: `$maestro` ou `/maestro` + tarefa.

### Regenerar manifest

Indexa `~/.cursor/skills`, `~/.agents/skills` e skills do projeto:

```bash
py -3 ~/.cursor/skills/maestro/scripts/build_manifest.py --project-root /caminho/do/projeto
```

### Buscar skills (prompt inteiro)

```bash
py -3 ~/.cursor/skills/maestro/scripts/search_skills.py "criar dashboard react" --json
```

Retorna `routing`, `confidence`, `mode`, `missing_skills`.

### Rotear sub-tarefas (apos decompor o grafo)

```bash
printf '%s\n' "design UI" "fix CI" | py -3 ~/.cursor/skills/maestro/scripts/route_tasks.py --json
```

## Testes

```bash
python -m unittest discover -s tests -v
```

CI roda automaticamente em push/PR na `main`.

## Estrutura

```text
maestro/
├── .github/workflows/ci.yml
├── docs/github-workflow.md
├── scripts/sync-templates.ps1
├── skills/maestro/
│   ├── SKILL.md
│   ├── community.yaml
│   ├── maestro-exclude.example.txt
│   └── scripts/
│       ├── build_manifest.py
│       ├── search_skills.py
│       ├── route_tasks.py
│       ├── routing.py
│       ├── intents.py
│       ├── synonyms.py
│       └── community.py
├── tests/
└── templates/
```

## Licenca

Uso interno. Ajuste conforme necessario.
