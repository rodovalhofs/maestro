import * as p from "@clack/prompts";
import { rmSync } from "node:fs";
import { join } from "node:path";
import { detectAgents, filterAgentsByFlags } from "./detect-agents.js";
import {
  commitSkillCopy,
  migrateLegacyFiles,
  rollbackSkillCopy,
  saveSetupConfig,
  stageSkillCopy,
} from "./install.js";
import { getMaestroPaths } from "./paths.js";
import { runBuildManifest } from "./run-manifest.js";

export async function runSetup(options) {
  const project = Boolean(options.project);
  const cwd = process.cwd();

  p.intro(project ? "Maestro setup (this project)" : "Maestro setup (global)");

  let agents = detectAgents({ project, cwd });
  agents = filterAgentsByFlags(agents, options);

  if (!options.cursor && !options.claude && !options.codex && !options.universal && !options.yes) {
    p.note(
      "↑↓ navegar · Espaço selecionar/desmarcar · Enter confirmar",
      "Atalhos do teclado",
    );

    const selected = await p.multiselect({
      message: "Which agents should receive the Maestro skill?",
      options: agents.map((a) => ({
        value: a.id,
        label: a.label,
        hint: a.detected ? `${a.skillsPath} (detected)` : a.skillsPath,
      })),
      required: true,
      initialValues: [],
    });
    if (p.isCancel(selected)) {
      p.cancel("Setup cancelled.");
      process.exit(0);
    }
    agents = agents.filter((a) => selected.includes(a.id));
  } else if (options.cursor || options.claude || options.codex || options.universal) {
    agents = filterAgentsByFlags(agents, options);
  } else if (options.yes) {
    agents = agents.filter((a) => a.detected);
  }

  if (!agents.length) {
    p.cancel("No agents selected.");
    process.exit(1);
  }

  const spinner = p.spinner();
  const paths = getMaestroPaths();
  const preflightOutput = join(paths.home, `.setup-preflight-${process.pid}.json`);
  spinner.start("Checking Python and local catalog access...");
  const preflight = runBuildManifest({
    projectRoot: cwd,
    quiet: true,
    output: preflightOutput,
  });
  rmSync(preflightOutput, { force: true });
  if (!preflight.ok) {
    spinner.stop("Local setup preflight failed");
    throw new Error(
      `${preflight.error}\nNothing was installed. Run: maestro-skills doctor`,
    );
  }
  spinner.stop("Local runtime ready");

  const installed = [];
  const transactions = [];

  for (const agent of agents) {
    spinner.start(`Installing Maestro for ${agent.label}…`);
    try {
      const transaction = stageSkillCopy(agent.skillsPath);
      transactions.push(transaction);
      const dest = transaction.dest;
      installed.push({ id: agent.id, label: agent.label, path: dest, skillsPath: agent.skillsPath });
      spinner.stop(`Installed → ${dest}`);
    } catch (err) {
      spinner.stop(`Failed for ${agent.label}`);
      p.log.error(String(err.message || err));
    }
  }

  if (!installed.length) {
    p.cancel("Setup failed — Maestro skill was not installed for any agent.");
    process.exit(1);
  }

  const migrated = migrateLegacyFiles();
  if (migrated.length) {
    p.log.info(`Migrated legacy files: ${migrated.join(", ")}`);
  }

  spinner.start("Building skills manifest…");
  const manifestResult = runBuildManifest({
    projectRoot: cwd,
    quiet: true,
    installedSkillPath: installed[0]?.path,
  });
  if (manifestResult.ok) {
    spinner.stop("Skills manifest ready");
  } else {
    spinner.stop("Manifest build failed");
    for (const transaction of transactions.reverse()) rollbackSkillCopy(transaction);
    throw new Error(
      `${manifestResult.error}\nInstallation changes were rolled back. ` +
        "Run: maestro-skills doctor",
    );
  }

  try {
    saveSetupConfig({
      installedAt: new Date().toISOString(),
      scope: project ? "project" : "global",
      projectRoot: project ? cwd : null,
      agents: installed,
      maestroHome: paths.home,
    });
  } catch (error) {
    for (const transaction of transactions.reverse()) rollbackSkillCopy(transaction);
    runBuildManifest({ projectRoot: cwd, quiet: true });
    throw new Error(`Setup registry failed; installation changes were rolled back: ${error.message}`);
  }

  for (const transaction of transactions) {
    try {
      commitSkillCopy(transaction);
    } catch (error) {
      p.log.warn(`Installed successfully but could not remove backup ${transaction.backup}: ${error.message}`);
    }
  }

  p.note(
    installed.map((i) => `${i.label}\n  ${i.path}`).join("\n\n"),
    "Installed paths",
  );
  p.outro("Maestro setup complete. Invoke with $maestro or /maestro in your agent.");
}

