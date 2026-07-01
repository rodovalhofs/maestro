#!/usr/bin/env node
import { Command } from "commander";
import { runRemove } from "../lib/remove.js";
import { runSetup } from "../lib/setup.js";

const program = new Command();

program
  .name("maestro-skills")
  .description("Install and configure the Maestro skill orchestrator for multiple AI agents")
  .version("0.1.0");

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

program.parseAsync(process.argv);
