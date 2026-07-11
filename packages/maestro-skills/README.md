# maestro-skills

Local-first installer and CLI for the Maestro skill router.

```bash
npx maestro-skills setup
npx maestro-skills doctor
npx maestro-skills search "fix CI"
```

Supported destinations: Cursor (`--cursor`), Claude Code (`--claude`), Codex
(`--codex`), and universal agent skills (`--universal`). Use `--project` to keep an
installation inside the current repository.

Search, route, manifest, doctor, setup, and remove run locally. Remote skill discovery
is opt-in and remote installation is never automatic.

Project: https://github.com/rodovalhofs/maestro
Security: https://github.com/rodovalhofs/maestro/blob/main/SECURITY.md
