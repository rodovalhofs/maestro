# Política de segurança

## Escopo

Este repositório contém a skill **Maestro** e scripts Python/Node que rodam **localmente** na máquina do usuário. Não há servidor proprietário, telemetria nem envio de dados da busca de skills para os mantenedores deste repo.

## O que o Maestro lê localmente

Para indexar skills instaladas, os scripts podem ler **somente metadados** (nome, descrição, tags) de:

| Pasta | Finalidade |
|-------|------------|
| `~/.cursor/skills` | Skills do Cursor |
| `~/.claude/skills` | Skills do Claude Code |
| `~/.codex/skills` | Skills do Codex |
| `~/.agents/skills` | Skills universais |
| `<projeto>/.cursor/skills` (e equivalentes) | Skills por projeto, se existirem |

**Gravação local:** `~/.maestro/skills-manifest.json`, `~/.maestro/skill-runbooks.user.json`, `~/.maestro/discover-allowlist.txt`, `~/.maestro/maestro-exclude.txt`.

Nenhum conteúdo dessas pastas é enviado automaticamente para a internet pelo Maestro.

## Discover e skills remotas

O fluxo **Discover** pode sugerir buscar skills em [skills.sh](https://skills.sh/) (`npx skills find`). **Instalar** (`npx skills add`) baixa código de repositórios GitHub de terceiros; o `SKILL.md` remoto passa a influenciar instruções do agente.

### Política (desde v0.1.3)

1. **Nunca** executar `npx skills add` automaticamente — apresente o comando para o usuário revisar e rodar manualmente.
2. **Não** use a flag `-y` em exemplos do fluxo Discover no `SKILL.md`.
3. Allowlist opcional: `~/.maestro/discover-allowlist.txt` (uma linha `owner/repo` por repo confiável). Mesmo na allowlist, instalação exige ação humana explícita.
4. Revise o código-fonte no GitHub antes de instalar qualquer skill sugerida.

Auditorias públicas em [skills.sh](https://www.skills.sh/rodovalhofs/maestro/maestro/security/agent-trust-hub) documentam esses vetores; as mitigações acima são intencionais.

## Runbooks e preflight

Runbooks podem instruir a executar CLIs **locais** (ex.: `ui-ux-pro-max` `search.py`). Só execute preflight documentado no runbook bundled ou em arquivos do usuário (`~/.maestro/`, `.maestro/`). Não invente comandos de skills não instaladas.

## Versões suportadas

| Versão | Suportada |
|--------|-----------|
| `main` | Sim |
| npm `maestro-skills` ≥ 0.1.3 | Sim |

## O que reportar

- Execução insegura de comandos ou path traversal nos scripts
- Leitura/escrita fora dos diretórios documentados sem consentimento
- Instruções no `SKILL.md` que contornem confirmação humana no Discover
- Vulnerabilidades em dependências de CI (GitHub Actions)

**Fora de escopo:** vulnerabilidades em skills de terceiros já instaladas na sua máquina; o IDE Cursor/Claude em si.

## Como reportar

1. **Não** abra Issue pública com detalhes de exploit.
2. Abra um [Security Advisory](https://github.com/rodovalhofs/maestro/security/advisories/new) **ou** canal privado com o mantenedor.
3. Inclua: versão/commit, SO, comando usado e impacto esperado.

Objetivo de resposta inicial: **7 dias úteis**.

## Boas práticas para quem instala

- Prefira `npx maestro-skills search` (CLI npm) em vez de paths manuais no PowerShell.
- Revise pacotes retornados por `npx skills find` antes de instalar.
- Use `~/.maestro/maestro-exclude.txt` para excluir skills sensíveis da busca.
- Não commite `skill-runbooks.user.json` com paths internos ou segredos em repositórios públicos.
- O script `scripts/sync-templates.ps1` **sobrescreve** `.github/` no destino — confira `-TargetRepo` antes de executar.
