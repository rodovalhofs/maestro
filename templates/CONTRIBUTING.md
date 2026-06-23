# Contribuicao — fluxo Issues + PR

## Regra geral

1. Abra ou referencie uma **Issue** descrevendo objetivo e escopo.
2. Crie branch `feat/<numero>-<slug>` ou `fix/<numero>-<slug>`.
3. Commits descritivos: `tipo(escopo): descricao` + `Refs #N` ou `Closes #N`.
4. Abra **PR draft**; quando CI e testes locais passarem, marque ready for review.
5. Merge na branch principal fecha a Issue (`Closes #N` no PR).

## CI — ordem obrigatoria

O pipeline roda **testes primeiro**, depois **build**. Se falhar:

- O PR nao deve ser mergeado.
- Abra ou atualize Issue com label `ci:falha` ate ficar verde.

## Project (opcional)

Se o time usar GitHub Projects, vincule Issues e PRs ao board do projeto.

Colunas sugeridas: Backlog → Em progresso → Em review → Concluido.
