# Contributing

Maestro is MIT-licensed and accepts focused bug fixes, routing improvements,
cross-platform fixes, security hardening, tests, and documentation.

## Local workflow

1. Create a branch such as `fix/catalog-isolation` or `feat/doctor-check`.
2. Add a behavior test that fails for the bug or requirement.
3. Change the canonical source:
   - Python engine and skill: `skills/maestro/`;
   - npm runtime: `packages/maestro-skills/`.
4. Synchronize generated package copies.
5. Run all validation locally.

```bash
node scripts/sync-skill-to-cli.mjs
python -m unittest discover -s tests -v
npm ci --prefix packages/maestro-skills
npm test --prefix packages/maestro-skills
npm run verify:packages
```

Do not edit `packages/*/skill/` directly. The scoped package runtime is generated from
`packages/maestro-skills/lib/` by the sync script.

## Compatibility

- Node.js 18+;
- Python 3.10+ using only the standard library in the runtime engine;
- Windows, macOS, and Linux;
- Cursor, Claude Code, Codex, and universal agent skill directories.

Keep local-only operations free of implicit network calls. New external effects must
be represented in output, disabled by default, and covered by consent-oriented tests.

## Pull requests

Explain the observed behavior, the intended behavior, security/privacy implications,
and the commands used to validate the change. Keep unrelated refactors separate.

For vulnerabilities, follow [SECURITY.md](SECURITY.md) and use a private advisory
instead of a public issue containing exploit details.
