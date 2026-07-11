import * as p from "@clack/prompts";
import { rmSync, existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { loadSetupConfig, pathIdentity, removeSkillFrom, writeSetupRegistry } from "./install.js";
import { getMaestroPaths } from "./paths.js";
import { detectAgents } from "./detect-agents.js";

const MAESTRO_HOME_FILES = [
  "skills-manifest.json",
  "maestro-exclude.txt",
  "config.json",
  "skill-runbooks.user.json",
  "discover-allowlist.txt",
];

export function cleanMaestroHome(home) {
  const removed = [];
  for (const name of MAESTRO_HOME_FILES) {
    const path = join(home, name);
    if (!existsSync(path)) continue;
    rmSync(path, { force: true });
    removed.push(name);
  }
  return removed;
}

export async function runRemove(options) {
  p.intro("Maestro remove");

  const config = loadSetupConfig();
  const projectRoot = options.project
    ? resolve(options.project === true ? process.cwd() : String(options.project))
    : null;
  let installations = config?.installations || [];
  if (projectRoot) {
    installations = installations.filter(
      (item) => item.scope === "project"
        && pathIdentity(item.projectRoot) === pathIdentity(projectRoot),
    );
  }
  let targets = installations.flatMap((installation, installationIndex) =>
    installation.agents.map((agent) => ({
      ...agent,
      targetId: `${installationIndex}:${agent.id}:${agent.skillsPath || agent.path}`,
    })),
  );

  if ((!targets.length && !projectRoot) || options.all) {
    const agents = detectAgents({ project: false });
    const detectedTargets = agents.filter((agent) => agent.detected).map((a) => ({
      id: a.id,
      targetId: `detected:${a.id}:${a.skillsPath}`,
      label: a.label,
      path: `${a.skillsPath}/maestro`.replace(/\\/g, "/"),
      skillsPath: a.skillsPath,
    }));
    const byPath = new Map(
      [...targets, ...detectedTargets].map((target) => [
        pathIdentity(target.skillsPath || dirname(target.path)),
        target,
      ]),
    );
    targets = [...byPath.values()];
  }

  if (!targets.length) {
    p.cancel(projectRoot
      ? `No Maestro installation registered for ${projectRoot}.`
      : "No Maestro installations found.");
    return;
  }

  if (!options.yes) {
    const selected = await p.multiselect({
      message: "Remove Maestro skill from:",
      options: targets.map((t) => ({
        value: t.targetId,
        label: t.label,
        hint: t.skillsPath || t.path,
      })),
      required: true,
      initialValues: targets.map((t) => t.targetId),
    });
    if (p.isCancel(selected)) {
      p.cancel("Remove cancelled.");
      process.exit(0);
    }
    targets = targets.filter((t) => selected.includes(t.targetId));
  }

  let cleanHome = false;
  if (!options.yes) {
    const clean = await p.confirm({
      message:
        "Also remove Maestro-owned home files (manifest, exclude, config, runbooks, allowlist)?",
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
    const dir = t.skillsPath || dirname(t.path);
    const removed = removeSkillFrom(dir);
    p.log.info(removed ? `Removed ${dir}/maestro` : `Not found: ${dir}/maestro`);
  }

  if (config) {
    const removedPaths = new Set(
      targets.map((target) => pathIdentity(target.skillsPath || dirname(target.path))),
    );
    const remaining = config.installations
      .map((installation) => ({
        ...installation,
        agents: installation.agents.filter((agent) =>
          !removedPaths.has(pathIdentity(agent.skillsPath || dirname(agent.path))),
        ),
      }))
      .filter((installation) => installation.agents.length > 0);
    writeSetupRegistry({ version: 2, installations: remaining });
  }

  if (cleanHome) {
    const { home } = getMaestroPaths();
    if (existsSync(home)) {
      const removed = cleanMaestroHome(home);
      p.log.info(
        removed.length
          ? `Removed ${removed.join(", ")} from ${home}`
          : `No Maestro-owned files found in ${home}`,
      );
    }
  }

  p.outro("Maestro removed.");
}
