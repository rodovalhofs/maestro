import * as p from "@clack/prompts";
import { detectAgents, filterAgentsByFlags } from "./detect-agents.js";
import {
  copySkillTo,
  migrateLegacyFiles,
  saveSetupConfig,
} from "./install.js";
import { getMaestroPaths } from "./paths.js";
import { registerOnSkillsSh, runBuildManifest } from "./run-manifest.js";

export async function runSetup(options) {
  const project = Boolean(options.project);
  const cwd = process.cwd();

  p.intro(project ? "Maestro setup (this project)" : "Maestro setup (global)");

  let agents = detectAgents({ project, cwd });
  agents = filterAgentsByFlags(agents, options);

  if (!options.cursor && !options.claude && !options.codex && !options.universal && !options.yes) {
    const selected = await p.multiselect({
      message: "Which agents should receive the Maestro skill?",
      options: agents.map((a) => ({
        value: a.id,
        label: a.label,
        hint: a.skillsPath,
      })),
      required: true,
      initialValues: agents.filter((a) => a.detected).map((a) => a.id),
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
    if (!agents.length) agents = detectAgents({ project, cwd });
  }

  if (!agents.length) {
    p.cancel("No agents selected.");
    process.exit(1);
  }

  let registerSkillsSh = false;
  if (!options.yes && !options.noSkillsRegistry) {
    const reg = await p.confirm({
      message: "Register install on skills.sh via npx skills add? (optional telemetry)",
      initialValue: false,
    });
    if (p.isCancel(reg)) {
      p.cancel("Setup cancelled.");
      process.exit(0);
    }
    registerSkillsSh = Boolean(reg);
  }

  const spinner = p.spinner();
  const installed = [];

  for (const agent of agents) {
    spinner.start(`Installing Maestro for ${agent.label}…`);
    try {
      const dest = copySkillTo(agent.skillsPath);
      installed.push({ id: agent.id, label: agent.label, path: dest });
      spinner.stop(`Installed → ${dest}`);
    } catch (err) {
      spinner.stop(`Failed for ${agent.label}`);
      p.log.error(String(err.message || err));
    }
  }

  const migrated = migrateLegacyFiles();
  if (migrated.length) {
    p.log.info(`Migrated legacy files: ${migrated.join(", ")}`);
  }

  spinner.start("Building skills manifest…");
  const manifestResult = runBuildManifest({ projectRoot: cwd, quiet: true });
  if (manifestResult.ok) {
    spinner.stop(manifestResult.message);
  } else {
    spinner.stop("Manifest build failed");
    p.log.warn(manifestResult.error);
  }

  if (registerSkillsSh) {
    spinner.start("Registering on skills.sh…");
    const reg = await registerOnSkillsSh(agents, { yes: options.yes });
    if (reg.ok && !reg.skipped) spinner.stop("Registered on skills.sh");
    else if (!reg.ok) {
      spinner.stop("skills.sh registration skipped");
      p.log.warn(reg.error);
    } else spinner.stop("No skills CLI agents selected");
  }

  const paths = getMaestroPaths();
  saveSetupConfig({
    version: 1,
    installedAt: new Date().toISOString(),
    scope: project ? "project" : "global",
    projectRoot: project ? cwd : null,
    agents: installed,
    maestroHome: paths.home,
  });

  p.note(
    installed.map((i) => `${i.label}\n  ${i.path}`).join("\n\n"),
    "Installed paths",
  );
  p.outro("Maestro setup complete. Invoke with $maestro or /maestro in your agent.");
}
