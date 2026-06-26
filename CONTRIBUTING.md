# Contribuindo

Obrigado pelo interesse no Maestro. Este projeto é open source (MIT).

## Como contribuir

1. Faça fork do repositório.
2. Crie uma branch: `feat/<slug>` ou `fix/<slug>`.
3. Para mudanças no motor de busca, inclua ou atualize testes em `tests/`.
4. Rode localmente:
   ```bash
   python -m unittest discover -s tests -v
   ```
5. Abra um Pull Request para `main` com descrição clara do que mudou e por quê.

## Áreas bem-vindas

- Melhorias no ranking (intents, sinônimos, domínios)
- Novos casos de teste com fixtures
- Documentação e exemplos em `community.yaml`
- Traduções ou clareza no README

## Estilo de código

- Python 3.12+ compatível
- Scripts em `skills/maestro/scripts/` devem permanecer sem dependências obrigatórias além da stdlib (PyYAML continua opcional)
- Mensagens de commit em português ou inglês, descritivas

## Segurança

Veja [SECURITY.md](SECURITY.md) para reporte responsável de vulnerabilidades.
