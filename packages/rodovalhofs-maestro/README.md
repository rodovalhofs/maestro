# @rodovalhofs/maestro

Scoped adapter for the local-first Maestro skill router. It exposes the same commands
as `maestro-skills` through the shorter `maestro` binary.

```bash
npx @rodovalhofs/maestro setup
npx @rodovalhofs/maestro doctor
npx @rodovalhofs/maestro search "fix CI"
```

Setup installs Maestro and Maestro Prompt Designer together. Prepare an approved
specification with Prompt Designer and your grilling skill, then execute Maestro
in the same conversation. Local task specifications stay outside npm packages.

The CLI remains offline. The agent reads candidate instructions and project evidence,
then researches confirmed gaps using public technical terms when network access is
allowed. Remote installation requires explicit approval. Use `--local-only` to
suppress external suggestions. Grilling is not bundled.

Version 0.3.0 replaces uncalibrated `confidence` with `evidence` and content-review
routing decisions. Both search and batch routing support the active project context.

Project: https://github.com/rodovalhofs/maestro
Security: https://github.com/rodovalhofs/maestro/blob/main/SECURITY.md
