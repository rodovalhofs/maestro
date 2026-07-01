import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = join(__dirname, "..");

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

export function skillSourceDir() {
  return join(PACKAGE_ROOT, "skill");
}

export function bundledBuildManifest() {
  return join(skillSourceDir(), "scripts", "build_manifest.py");
}
