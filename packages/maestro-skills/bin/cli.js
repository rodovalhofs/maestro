#!/usr/bin/env node
import { Command } from "commander";
import { runRemove } from "../lib/remove.js";
import { runSetup } from "../lib/setup.js";
import { runSearch, runRoute } from "../lib/commands.js";
import { runBuildManifest } from "../lib/python.js";
import {
  addRunbook,
  discoverAllowlistExample,
  discoverAllowlistPath,
  editRunbookHint,
  listRunbooks,
} from "../lib/runbook.js";
import { existsSync, writeFileSync } from "node:fs";
import { mkdirSync } from "node:fs";
import { dirname } from "node:path";

const program = new Command();

program
  .name("maestro-skills")
  .description("Install and configure the Maestro skill orchestrator for multiple AI agents")
  .version("0.1.3");

program
  .command("setup")
  .description("Interactive setup — choose agents, scope, and build manifest")
  .option("--project", "Install only in the current project")
  .option("--cursor", "Target Cursor only")
  .option("--claude", "Target Claude Code only")
  .option("--codex", "Target Codex only")
  .option("--universal", "Target ~/.agents/skills only")
  .option("-y, --yes", "Skip prompts (defaults: detected agents, no skills.sh)")
  .option("--no-skills-registry", "Skip skills.sh registration prompt")
  .action(async (opts) => {
    await runSetup(opts);
  });

program
  .command("remove")
  .description("Remove Maestro skill from selected agents")
  .option("-y, --yes", "Remove from all last-known destinations without prompts")
  .option("--all", "Consider all known agent paths")
  .option("--clean-home", "With --yes, also remove ~/.maestro/")
  .action(async (opts) => {
    await runRemove(opts);
  });

program
  .command("search")
  .description("Search local skills (shell-safe; works in PowerShell)")
  .argument("<query>", "Prompt to match against installed skills")
  .option("--domain <domain>", "Domain bucket filter")
  .option("--project-root <path>", "Project root for runbook merge")
  .option("--project-name <name>", "Project display name for design-system -p")
  .option("--max-results <n>", "Max results", "5")
  .action((query, opts) => {
    const result = runSearch(query, {
      domain: opts.domain,
      projectRoot: opts.projectRoot || process.cwd(),
      projectName: opts.projectName,
      maxResults: Number(opts.maxResults),
    });
    if (!result.ok) {
      console.error(result.error);
      process.exit(result.code || 1);
    }
    console.log(JSON.stringify(result.data, null, 2));
  });

program
  .command("route")
  .description("Route multiple sub-tasks to skills (stdin or --task)")
  .option("--task <task>", "Single task (repeatable)", (v, acc = []) => acc.concat(v), [])
  .option("--domain <domain>", "Domain bucket filter")
  .action((opts) => {
    const tasks = opts.task?.length ? opts.task : null;
    if (!tasks) {
      console.error("Provide at least one --task \"...\"");
      process.exit(1);
    }
    const result = runRoute(tasks, { domain: opts.domain });
    if (!result.ok) {
      console.error(result.error);
      process.exit(1);
    }
    console.log(JSON.stringify(result.data, null, 2));
  });

program
  .command("manifest")
  .description("Rebuild ~/.maestro/skills-manifest.json")
  .option("--project-root <path>", "Project root", process.cwd())
  .action((opts) => {
    const result = runBuildManifest({ projectRoot: opts.projectRoot, quiet: false });
    if (!result.ok) {
      console.error(result.error);
      process.exit(result.code || 1);
    }
  });

const runbook = program.command("runbook").description("Manage user skill runbooks");

runbook
  .command("list")
  .description("List user runbook entries")
  .action(() => {
    const { path, names } = listRunbooks();
    console.log(`User runbooks: ${path}`);
    if (!names.length) {
      console.log("(empty — use: maestro-skills runbook add <skill>)");
      return;
    }
    for (const name of names) console.log(`- ${name}`);
  });

runbook
  .command("add")
  .description("Add a user runbook entry")
  .argument("<skill>", "Skill name (as in manifest)")
  .option("--summary <text>", "Short description")
  .option("--notes <text>", "Graph hint / notes")
  .action((skill, opts) => {
    try {
      const { path, skill: entry } = addRunbook(skill, {
        summary: opts.summary,
        notes: opts.notes,
      });
      console.log(`Created ${path} → skills.${skill}`);
      console.log(JSON.stringify(entry, null, 2));
    } catch (err) {
      console.error(String(err.message || err));
      process.exit(1);
    }
  });

runbook
  .command("edit")
  .description("Show path and schema to edit a runbook entry")
  .argument("<skill>", "Skill name")
  .action((skill) => {
    const info = editRunbookHint(skill);
    console.log(info.hint);
    console.log(JSON.stringify(info.example, null, 2));
  });

runbook
  .command("init-allowlist")
  .description("Create ~/.maestro/discover-allowlist.txt template")
  .action(() => {
    const path = discoverAllowlistPath();
    if (existsSync(path)) {
      console.log(`Already exists: ${path}`);
      return;
    }
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, discoverAllowlistExample(), "utf8");
    console.log(`Created ${path}`);
  });

program.parseAsync(process.argv);
