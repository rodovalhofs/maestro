import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = resolve(__dirname, "..");

export function getMaestroHome() {
  return process.env.MAESTRO_HOME || join(homedir(), ".maestro");
}

export function getMaestroPaths() {
  const home = getMaestroHome();
  return {
    home,
    manifest: join(home, "skills-manifest.json"),
    exclude: join(home, "maestro-exclude.txt"),
    config: join(home, "config.json"),
    legacyManifest: join(homedir(), ".cursor", "skills-manifest.json"),
    legacyExclude: join(homedir(), ".cursor", "maestro-exclude.txt"),
  };
}

export function loadAgents() {
  const raw = readFileSync(join(PACKAGE_ROOT, "agents.json"), "utf8");
  return JSON.parse(raw).agents;
}

export function resolveSkillsDir(agent, { project = false, cwd = process.cwd() } = {}) {
  const base = project ? cwd : homedir();
  const rel = project ? agent.projectSkillsDir : agent.globalSkillsDir;
  return join(base, rel);
}

/** Resolve bundled skill folder (works for npm pack and monorepo-root publish). */
export function skillSourceDir() {
  const candidates = [];

  let dir = PACKAGE_ROOT;
  for (let i = 0; i < 5; i++) {
    candidates.push(
      join(dir, "skill"),
      join(dir, "skills", "maestro"),
    );
    dir = resolve(dir, "..");
  }

  for (const candidate of candidates) {
    if (existsSync(join(candidate, "SKILL.md"))) {
      return candidate;
    }
  }

  throw new Error(
    `Skill source not found (expected SKILL.md under ${join(PACKAGE_ROOT, "skill")}). ` +
      "Reinstall with: npx maestro-skills@latest setup",
  );
}

export function bundledBuildManifest() {
  return join(skillSourceDir(), "scripts", "build_manifest.py");
}
