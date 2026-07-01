import * as p from "@clack/prompts";
import { rmSync, existsSync } from "node:fs";
import { loadSetupConfig, removeSkillFrom } from "./install.js";
import { getMaestroPaths } from "./paths.js";
import { detectAgents } from "./detect-agents.js";

export async function runRemove(options) {
  p.intro("Maestro remove");

  const config = loadSetupConfig();
  let targets = config?.agents || [];

  if (!targets.length || options.all) {
    const agents = detectAgents({ project: false });
    targets = agents.map((a) => ({
      id: a.id,
      label: a.label,
      path: `${a.skillsPath}/maestro`.replace(/\\/g, "/"),
      skillsPath: a.skillsPath,
    }));
  }

  if (!options.yes) {
    const selected = await p.multiselect({
      message: "Remove Maestro skill from:",
      options: targets.map((t) => ({
        value: t.id,
        label: t.label,
        hint: t.skillsPath || t.path,
      })),
      required: true,
      initialValues: targets.map((t) => t.id),
    });
    if (p.isCancel(selected)) {
      p.cancel("Remove cancelled.");
      process.exit(0);
    }
    targets = targets.filter((t) => selected.includes(t.id));
  }

  let cleanHome = false;
  if (!options.yes) {
    const clean = await p.confirm({
      message: "Also remove ~/.maestro/ (manifest, exclude, config)?",
      initialValue: false,
    });
    if (p.isCancel(clean)) {
      p.cancel("Remove cancelled.");
      process.exit(0);
    }
    cleanHome = Boolean(clean);
  } else if (options.cleanHome) {
    cleanHome = true;
  }

  for (const t of targets) {
    const dir = t.skillsPath || t.path.replace(/\/maestro$/, "");
    const removed = removeSkillFrom(dir);
    p.log.info(removed ? `Removed ${dir}/maestro` : `Not found: ${dir}/maestro`);
  }

  if (cleanHome) {
    const { home } = getMaestroPaths();
    if (existsSync(home)) {
      rmSync(home, { recursive: true, force: true });
      p.log.info(`Removed ${home}`);
    }
  }

  p.outro("Maestro removed.");
}
