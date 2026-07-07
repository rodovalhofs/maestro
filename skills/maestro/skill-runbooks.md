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

---

## ui-ux-pro-max

Skill path (typical): `~/.agents/skills/ui-ux-pro-max/` or `~/.cursor/skills/ui-ux-pro-max/`

Scripts live in `{skill_root}/scripts/search.py`. **Requires Python 3.**

### When Maestro should route here

Use when the task changes how something **looks, feels, moves, or is interacted with**:

- Dashboard, landing page, admin panel, e-commerce, SaaS UI
- Components: buttons, modals, forms, tables, charts, navigation
- Design review, accessibility, dark mode, responsive layout

**Skip** for pure backend/API/DB/DevOps.

### Grafo Maestro (obrigatorio)

```text
1. Explore / context (se repo novo)
2a. Preflight design-system [ui-ux-pro-max]  <- parent executa CLI abaixo
2b. Implement UI [ui-ux-pro-max]             <- subagente le SKILL.md + stdout do 2a
3. GitHub (se repo versionado)
```

Parent **executa** o preflight e cola a saida no prompt do subagente. Se falhar, nao spawnar 2b.

### Step 1 — Analisar o prompt

Extrair do pedido do usuario:

| Campo | Exemplos |
|-------|----------|
| Product type | SaaS, dashboard, landing, e-commerce, mobile app |
| Audience | internal ops, end consumer, B2B |
| Style | minimal, dark mode, dense dashboard, glassmorphism |
| Stack | react, nextjs, shadcn, vue, tailwind |

### Step 2 — Design system (OBRIGATORIO)

Sempre comecar com `--design-system`:

**Windows (PowerShell):**

```powershell
py -3 "$env:USERPROFILE\.agents\skills\ui-ux-pro-max\scripts\search.py" "<produto> <industria> <keywords>" --design-system -p "<ProjectName>"
```

**Com placeholders do runbook (apos `npx maestro-skills search`):**

```powershell
py -3 "{skill_scripts}/search.py" "{query}" --design-system -p "{project_name}"
```

**Unix:**

```bash
python3 ~/.agents/skills/ui-ux-pro-max/scripts/search.py "<query>" --design-system -p "<ProjectName>"
```

**Exemplo (dashboard interno):**

```powershell
py -3 "$env:USERPROFILE\.agents\skills\ui-ux-pro-max\scripts\search.py" "internal analytics dashboard saas minimal" --design-system -p "ComprasPJ"
```

**Dashboard denso (dials opcionais 1-10):**

```powershell
py -3 "$env:USERPROFILE\.agents\skills\ui-ux-pro-max\scripts\search.py" "internal analytics dashboard" --design-system --variance 8 --motion 7 --density 8 -p "ComprasPJ"
```

| Dial | Baixo (1-3) | Alto (8-10) |
|------|-------------|-------------|
| `--variance` | Minimal, centrado | Bold, bento/asimetrico |
| `--motion` | Micro-interacoes | Coreografia complexa + snippet GSAP |
| `--density` | Espacoso (marketing) | Denso (dashboard) |

### Step 2b — Persistir no projeto (opcional)

Para tokens reutilizaveis entre sessoes (commitar `design-system/` no git):

```powershell
py -3 "$env:USERPROFILE\.agents\skills\ui-ux-pro-max\scripts\search.py" "<query>" --design-system --persist -p "ComprasPJ"
```

Pagina especifica:

```powershell
py -3 "$env:USERPROFILE\.agents\skills\ui-ux-pro-max\scripts\search.py" "<query>" --design-system --persist -p "ComprasPJ" --page "dashboard"
```

Hierarquia:

1. `design-system/pages/<page>.md` (se existir) **sobrescreve**
2. Senao `design-system/MASTER.md`

Prompt para o subagente apos persist:

```text
Read design-system/MASTER.md and design-system/pages/<page>.md if it exists.
Prioritize the page file over Master. Then implement...
```

### Step 3 — Buscas complementares (antes de codar)

Depois do design system, se precisar de detalhe:

```powershell
# UX / acessibilidade
py -3 "$env:USERPROFILE\.agents\skills\ui-ux-pro-max\scripts\search.py" "forms accessibility animation" --domain ux

# Graficos em dashboard
py -3 "$env:USERPROFILE\.agents\skills\ui-ux-pro-max\scripts\search.py" "real-time dashboard kpi" --domain chart

# Stack do projeto
py -3 "$env:USERPROFILE\.agents\skills\ui-ux-pro-max\scripts\search.py" "list performance suspense" --stack nextjs

# shadcn
py -3 "$env:USERPROFILE\.agents\skills\ui-ux-pro-max\scripts\search.py" "composition primitives" --stack shadcn
```

| Dominio `--domain` | Uso |
|--------------------|-----|
| `ux` | A11y, animacao, forms, loading |
| `style` | glassmorphism, minimalism, dark mode |
| `color` | Paletas por tipo de produto |
| `typography` | Pares de fontes |
| `chart` | Tipo de grafico para dados |
| `landing` | Hero, pricing, social proof |
| `product` | Padroes por vertical |
| `google-fonts` | Fonte especifica |
| `prompt` | Keywords CSS |

### Step 4 — Validacao pre-entrega

```powershell
py -3 "$env:USERPROFILE\.agents\skills\ui-ux-pro-max\scripts\search.py" "animation accessibility z-index loading" --domain ux
```

Checklist rapido no `SKILL.md`: contraste 4.5:1, touch 44px, focus visible, sem emoji como icone, reduced-motion.

### Maestro + ui-ux-pro-max (fluxo completo)

```bash
# 1. Maestro encontra a skill e anexa runbook
npx maestro-skills search "melhorar dashboard indicadores UI" --domain design --json

# 2. No JSON, results[].runbook traz preflight com resolved_args
# 3. Parent executa preflight (design-system)
# 4. Subagente implementa com SKILL.md + saida do CLI
```

`--project-name` no Maestro search define o `-p` do design system:

```bash
npx maestro-skills search "dashboard indicadores" --domain design --project-name "ComprasPJ" --json
```

---

## grilling

Interview node: one question per turn, include your recommended answer, wait for user reply.

## canvas

Use when the deliverable is a visual/analytical artifact (dashboard, audit, timeline) instead of plain markdown.

## _example

Copy this entry as a template for custom skills. Do not reference private paths or secrets in public runbooks.
