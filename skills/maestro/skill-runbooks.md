# Skill runbooks

Runbooks attach validated preflight metadata to a search result. Maestro resolves
placeholders but does not execute the command itself.

## Merge and trust

Sources merge in this order:

1. bundled `skill-runbooks.json`;
2. `~/.maestro/skill-runbooks.user.json`;
3. `<project>/.maestro/skill-runbooks.json`.

Later entries override earlier fields. Every attached entry includes `provenance`.
Invalid JSON, oversized files, invalid effects, and malformed preflights are reported
in `runbooks.errors` and skipped.

Trust policy:

| Source/effect | Default |
|---------------|---------|
| bundled + required + `read_local` | may run after graph approval |
| user or project source | explicit preflight approval |
| `write_workspace` | explicit write approval |
| `network`, `install_remote` | explicit network/install approval |
| `git_commit`, `publish_external`, `unknown` | explicit effect approval |

Project runbooks are repository-controlled input. Review them like build scripts.

## Schema

```json
{
  "version": 1,
  "skills": {
    "my-skill": {
      "summary": "Run local lint before implementation",
      "graph_hint": "Preflight lint -> implement",
      "preflight": [
        {
          "id": "lint",
          "label": "Lint package",
          "command": "npm",
          "args": ["run", "lint"],
          "effect": "read_local",
          "required": false,
          "notes": "Run from project root"
        }
      ]
    }
  }
}
```

Allowed effects: `read_local`, `write_workspace`, `network`, `install_remote`,
`git_commit`, `publish_external`, and `unknown`.

Use the structured `resolved_command` and `resolved_args` returned by search. Pass
them directly to a process API with shell execution disabled. Do not interpolate a
shell command string.

## Placeholders

| Placeholder | Value |
|-------------|-------|
| `{skill_root}` | directory containing the selected `SKILL.md` |
| `{skill_scripts}` | `<skill_root>/scripts` |
| `{query}` | original local query |
| `{project_name}` | explicit project name or project folder name |

Platform overrides may replace the executable and add an argument prefix:

```json
{
  "command": "python3",
  "args": ["{skill_scripts}/search.py", "{query}"],
  "platforms": {
    "win32": { "command": "py", "args_prefix": ["-3"] },
    "default": { "command": "python3", "args_prefix": [] }
  }
}
```

## User commands

```bash
npx maestro-skills runbook list
npx maestro-skills runbook add my-skill --summary "Local lint" --notes "Run before implementation"
npx maestro-skills runbook edit my-skill
```

`runbook add` creates an inert entry with no preflight commands. Edit the JSON to add
commands and effects.

## Bundled UI preflight

The bundled `ui-ux-pro-max` entry contains:

- required `design-system`: read-only, with `py -3` on Windows and `python3` elsewhere;
- optional `design-system-persist`: writes into the project and requires approval.

When present in a search result, use its resolved fields instead of copying a
machine-specific path from documentation. Attach read-only stdout to the dependent
implementation node. A required failure blocks that node; an optional failure does not
block unrelated work.
