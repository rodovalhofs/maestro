# maestro-skills

Installer and local retrieval CLI for Maestro and Maestro Prompt Designer.

```bash
npx maestro-skills setup
npx maestro-skills doctor
npx maestro-skills search "fix CI"
```

Supported destinations: Cursor (`--cursor`), Claude Code (`--claude`), Codex
(`--codex`), and universal agent skills (`--universal`). Use `--project` to keep an
installation inside the current repository.

Setup installs both skills. Use grilling with `$maestro-prompt-designer` to prepare
and save an approved task specification, then invoke `$maestro` in the same
conversation. Maestro reads relevant project context and candidate instructions,
explains its selection and executes approved phases through completion.

The CLI runs locally. The agent researches confirmed capability gaps or requested
alternatives using minimal public technical queries. `--local-only` suppresses
research suggestions; user network restrictions take precedence. Installation of
remote skills requires explicit approval. Grilling is not bundled.

In 0.3.0, JSON `confidence` is replaced by metadata `evidence`; scores never authorize
loading. `routing.decision` requests content review, comparison, no-match handling
or bypass. Both `search` and `route` support `--project-root` and `--local-only`.
Task specifications are private local project files and are excluded from releases.

Project: https://github.com/rodovalhofs/maestro
Security: https://github.com/rodovalhofs/maestro/blob/main/SECURITY.md
