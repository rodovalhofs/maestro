# GitHub — fluxo generico (Issues + PR + CI)

Guia reutilizavel para qualquer repositorio versionado. Copie `templates/` para o seu projeto ou use `scripts/sync-templates.ps1`.

## Fluxo diario

```text
Issue → branch feat/N-slug → testes locais → build local → push → PR → CI → merge → Issue fecha
```

### Branch

- Prefixo: `feat/` ou `fix/`
- Exemplo: `feat/12-dashboard-indicadores`
- Nunca commitar direto na branch principal (`main` ou `master`)

### Commits

- Mensagem clara em portugues (ou idioma do time): `tipo(escopo): descricao`
- Referencie a Issue: `Refs #N` no corpo ou `Closes #N` quando o PR fecha a Issue

### Pull request

1. Abra PR em **draft** enquanto trabalha
2. Rode testes e build localmente antes de marcar ready for review
3. CI deve ficar verde antes do merge
4. Use `Closes #N` no PR para fechar a Issue automaticamente

## CI (GitHub Actions)

Ordem recomendada em qualquer repo:

1. **test** — testes automatizados
2. **build** — compila frontend, empacota artefato, etc. (so se test passou)

Falha no CI:

- Workflow `ci-failure-to-issue.yml` pode abrir Issue com label `ci:falha`
- Corrija na mesma branch/PR ate verde
- Nao mergear com CI vermelho

### Adaptar ao seu stack

Edite `templates/.github/workflows/ci.yml`:

- **Node/React:** `npm ci && npm test` / `npm run build`
- **Python:** `pip install -r requirements.txt && pytest`
- **Go:** `go test ./...` / `go build ./...`

Mantenha a ordem: job `test` antes do job `build`.

## Project (opcional)

Para times que usam GitHub Projects:

| Coluna | Quando usar |
|--------|-------------|
| Backlog | Issue aberta, sem branch |
| Em progresso | Branch criada, PR draft |
| Em review | PR ready, CI verde |
| Concluido | Merge na branch principal |

```bash
gh project create --owner <org-ou-user> --title "Meu projeto"
gh project link <NUMERO> --owner <org-ou-user> --repo <repo>
```

## Labels sugeridas

Veja `templates/labels.json`. Aplicar com:

```bash
gh label create -f templates/labels.json  # ou script proprio
```

## Manutencao dos templates

```powershell
cd C:\Projetos\maestro
.\scripts\sync-templates.ps1 -TargetRepo "C:\caminho\do\seu\projeto"
```

Nao versione `templates/` dentro de cada repo de aplicacao; copie para `.github/` local.

## Skills relacionadas (Cursor)

Para agentes que orquestram esse fluxo:

- `github` — triagem de Issues e PRs
- `yeet` — commit, push e PR draft
- `gh-fix-ci` — depurar checks do GitHub Actions
