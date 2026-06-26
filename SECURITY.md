# Política de segurança

## Escopo

Este repositório contém a skill **Maestro** e scripts Python/PowerShell que rodam **localmente** na máquina do usuário. Eles leem pastas de skills (`~/.cursor/skills`, `~/.agents/skills`) e gravam um manifest em `~/.cursor/skills-manifest.json`. Não há servidor, telemetria nem envio de dados para terceiros.

## Versões suportadas

| Versão | Suportada |
|--------|-----------|
| `main` | Sim |

## O que reportar

- Execução insegura de comandos ou path traversal nos scripts
- Leitura/escrita fora dos diretórios documentados sem consentimento do usuário
- Vulnerabilidades em dependências usadas em CI (GitHub Actions)

**Não** é escopo deste repo: vulnerabilidades em skills de terceiros instaladas na sua máquina, nem no Cursor IDE em si.

## Como reportar

1. **Não** abra Issue pública com detalhes de exploit.
2. Abra um [Security Advisory](https://github.com/rodovalhofs/maestro/security/advisories/new) no GitHub **ou** envie descrição e passos de reprodução por canal privado acordado com o mantenedor.
3. Inclua: versão/commit, SO, comando usado e impacto esperado.

Objetivo de resposta inicial: **7 dias úteis**.

## Boas práticas para quem instala

- Revise `community.yaml` antes de confiar em `install_hint` de skills sugeridas.
- Use `~/.cursor/maestro-exclude.txt` para excluir skills sensíveis da busca.
- O script `scripts/sync-templates.ps1` **sobrescreve** `.github/` no repositório destino — confira o `-TargetRepo` antes de executar.
