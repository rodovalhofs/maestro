# Skill runbooks

Maestro attaches **runbooks** to search results when a matched skill needs extra CLI steps before subagents run.

## Merge order

1. Bundled `skill-runbooks.json` (shipped with Maestro)
2. `~/.maestro/skill-runbooks.user.json` (per user, all projects)
3. `<project>/.maestro/skill-runbooks.json` (optional, version in your repo)

Later sources override fields on the same skill name.

## User overrides

```bash
npx maestro-skills runbook list
npx maestro-skills runbook add my-skill --notes "Run lint before deploy"
npx maestro-skills runbook edit my-skill
```

Or create `~/.maestro/skill-runbooks.user.json`:

```json
{
  "skills": {
    "my-custom-skill": {
      "summary": "What this skill needs",
      "preflight": [
        {
          "id": "lint",
          "label": "Lint package",
          "command": "npm",
          "args": ["run", "lint"],
          "notes": "Run from project root"
        }
      ]
    }
  }
}
```

## Preflight placeholders

| Placeholder | Value |
|-------------|--------|
| `{skill_root}` | Directory containing the skill's `SKILL.md` |
| `{skill_scripts}` | `{skill_root}/scripts` |
| `{query}` | Original Maestro user prompt |
| `{project_name}` | Project folder name or `-p` value |

## Bundled skills

### ui-ux-pro-max

Before UI work, run design-system generation:

```bash
python "{skill_scripts}/search.py" "<product query>" --design-system -p "<ProjectName>"
```

On Windows PowerShell, prefer:

```bash
npx maestro-skills search "<query>" --domain design --json
```

Then add graph nodes: **Preflight design-system** → **Implement UI**.

### grilling

Interview node: one question per turn, include your recommended answer, wait for user reply.

### canvas

Use when the deliverable is a visual/analytical artifact (dashboard, audit, timeline) instead of plain markdown.

### _example

Copy this entry as a template for custom skills. Do not reference private paths or secrets in public runbooks.
