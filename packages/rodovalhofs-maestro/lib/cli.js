import { Command } from "commander";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";

import { runSearch, runRoute } from "./commands.js";
import { formatDoctor, runDoctorChecks } from "./doctor.js";
import { packageVersion } from "./paths.js";
import { runBuildManifest } from "./python.js";
import { runRemove } from "./remove.js";
import {
  addRunbook,
  discoverAllowlistExample,
  discoverAllowlistPath,
  editRunbookHint,
  listRunbooks,
} from "./runbook.js";
import { runSetup } from "./setup.js";

export function createProgram({
  name = "maestro-skills",
  description = "Install and configure the Maestro skill orchestrator for multiple AI agents",
} = {}) {
  const program = new Command();
  program.name(name).description(description).version(packageVersion());

  program
    .command("setup")
    .description("Interactive setup — choose agents, scope, and build manifest")
    .option("--project", "Install only in the current project")
    .option("--cursor", "Target Cursor only")
    .option("--claude", "Target Claude Code only")
    .option("--codex", "Target Codex only")
    .option("--universal", "Target ~/.agents/skills only")
    .option("-y, --yes", "Skip prompts (requires detected agents or explicit flags)")
    .action(runSetup);

  program
    .command("remove")
    .description("Remove Maestro skill from selected agents")
    .option("-y, --yes", "Remove from all last-known destinations without prompts")
    .option("--all", "Consider all known agent paths")
    .option("--project [path]", "Remove only one project installation (default: current directory)")
    .option("--clean-home", "With --yes, remove only Maestro-owned home files")
    .action(runRemove);

  program
    .command("search")
    .description("Search local skills (shell-safe; works in PowerShell)")
    .argument("<query>", "Prompt to match against installed skills")
    .option("--domain <domain>", "Domain signal")
    .option("--project-root <path>", "Project root for catalog overlay and runbooks")
    .option("--project-name <name>", "Project display name for design-system -p")
    .option("--max-results <n>", "Max results", "5")
    .option("--json", "Emit full JSON")
    .action((query, opts) => {
      const maxResults = Number(opts.maxResults);
      if (!Number.isInteger(maxResults) || maxResults < 1 || maxResults > 20) {
        console.error("--max-results must be an integer from 1 to 20");
        process.exitCode = 1;
        return;
      }
      const result = runSearch(query, {
        domain: opts.domain,
        projectRoot: opts.projectRoot || process.cwd(),
        projectName: opts.projectName,
        maxResults,
      });
      if (!result.ok) {
        console.error(result.error);
        process.exitCode = result.code || 1;
        return;
      }
      console.log(opts.json ? JSON.stringify(result.data, null, 2) : formatSearch(result.data));
    });

  program
    .command("route")
    .description("Route multiple sub-tasks to skills (stdin or --task)")
    .option("--task <task>", "Single task (repeatable)", (value, acc = []) => acc.concat(value), [])
    .option("--domain <domain>", "Domain signal")
    .option("--json", "Emit full JSON")
    .action(async (opts) => {
      let tasks;
      try {
        tasks = opts.task?.length ? opts.task : await readTasksFromStdin();
        validateTasks(tasks);
      } catch (error) {
        console.error(String(error.message || error));
        process.exitCode = 1;
        return;
      }
      if (!tasks.length) {
        console.error('Provide at least one --task "..." or newline-delimited tasks on stdin');
        process.exitCode = 1;
        return;
      }
      const result = runRoute(tasks, { domain: opts.domain });
      if (!result.ok) {
        console.error(result.error);
        process.exitCode = result.code || 1;
        return;
      }
      console.log(opts.json ? JSON.stringify(result.data, null, 2) : formatRoute(result.data));
    });

  program
    .command("manifest")
    .description("Rebuild ~/.maestro/skills-manifest.json")
    .option("--project-root <path>", "Project root", process.cwd())
    .action((opts) => {
      const result = runBuildManifest({ projectRoot: opts.projectRoot, quiet: false });
      if (!result.ok) {
        console.error(result.error);
        process.exitCode = result.code || 1;
      }
    });

  program
    .command("doctor")
    .description("Validate the local Maestro installation without network access")
    .option("--json", "Emit full JSON")
    .action((opts) => {
      const result = runDoctorChecks();
      console.log(opts.json ? JSON.stringify(result, null, 2) : formatDoctor(result));
      if (!result.ok) process.exitCode = 1;
    });

  const runbook = program.command("runbook").description("Manage user skill runbooks");

  runbook
    .command("list")
    .description("List user runbook entries")
    .action(() => {
      try {
        const { path, names } = listRunbooks();
        console.log(`User runbooks: ${path}`);
        if (!names.length) {
          console.log(`(empty — use: ${name} runbook add <skill>)`);
          return;
        }
        for (const skillName of names) console.log(`- ${skillName}`);
      } catch (error) {
        console.error(String(error.message || error));
        process.exitCode = 1;
      }
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
        console.log(`Created ${path} -> skills.${skill}`);
        console.log(JSON.stringify(entry, null, 2));
      } catch (error) {
        console.error(String(error.message || error));
        process.exitCode = 1;
      }
    });

  runbook
    .command("edit")
    .description("Show path and schema to edit a runbook entry")
    .argument("<skill>", "Skill name")
    .action((skill) => {
      try {
        const info = editRunbookHint(skill);
        console.log(info.hint);
        console.log(JSON.stringify(info.example, null, 2));
      } catch (error) {
        console.error(String(error.message || error));
        process.exitCode = 1;
      }
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

  return program;
}

export async function runCli(options = {}) {
  const program = createProgram(options);
  try {
    await program.parseAsync(options.argv || process.argv);
  } catch (error) {
    console.error(String(error.message || error));
    process.exitCode = Number.isInteger(error.exitCode) ? error.exitCode : 1;
  }
}

async function readTasksFromStdin() {
  if (process.stdin.isTTY) return [];
  let input = "";
  process.stdin.setEncoding("utf8");
  for await (const chunk of process.stdin) {
    input += chunk;
    if (input.length > 100_000) throw new Error("Task input exceeds 100000 characters");
  }
  return input
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function validateTasks(tasks) {
  if (tasks.length > 100) throw new Error("Route accepts at most 100 tasks");
  if (tasks.some((task) => task.length > 10_000)) {
    throw new Error("Each route task must be at most 10000 characters");
  }
}

function formatSearch(payload) {
  const routing = payload.routing || {};
  const lines = [
    `Domain: ${payload.domain_label} (${payload.domain})`,
    `Routing: ${routing.priority || "-"} / ${routing.decision || "-"}`,
    `Weak match: ${payload.weak_match ? "yes" : "no"}`,
  ];
  if (payload.discover?.triggered) {
    lines.push(`Discover: ${payload.discover.reasons.join(", ")} (network consent required)`);
  }
  lines.push("");
  for (const [index, skill] of (payload.results || []).entries()) {
    lines.push(`${index + 1}. ${skill.name} [${skill.mode}] score=${skill.score}`);
    lines.push(`   ${skill.path}`);
  }
  if (!payload.results?.length) lines.push("No local skill matched.");
  return lines.join("\n");
}

function formatRoute(payload) {
  const lines = [`Tasks: ${payload.task_count || payload.results?.length || 0}`, ""];
  for (const [index, item] of (payload.results || []).entries()) {
    const top = item.results?.[0];
    lines.push(`${index + 1}. ${item.task || item.query}: ${top?.name || "no local match"}`);
  }
  return lines.join("\n");
}
