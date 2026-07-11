import { randomUUID } from "node:crypto";
import { cpSync, existsSync, mkdirSync, readFileSync, renameSync, rmSync } from "node:fs";
import { basename, dirname, join, resolve } from "node:path";
import { writeFileAtomic } from "./atomic-file.js";
import { getMaestroPaths, skillSourceDir } from "./paths.js";

export function copySkillTo(destDir) {
  const transaction = stageSkillCopy(destDir);
  commitSkillCopy(transaction);
  return transaction.dest;
}

export function stageSkillCopy(destDir) {
  const src = skillSourceDir();
  const dest = join(destDir, "maestro");
  const token = `${process.pid}-${randomUUID()}`;
  const staging = join(destDir, `.maestro-stage-${token}`);
  const backup = join(destDir, `.maestro-backup-${token}`);

  mkdirSync(dirname(dest), { recursive: true });
  try {
    cpSync(src, staging, { recursive: true, errorOnExist: true });
    const pycache = join(staging, "scripts", "__pycache__");
    if (existsSync(pycache)) rmSync(pycache, { recursive: true, force: true });
    if (existsSync(dest)) renameSync(dest, backup);
    renameSync(staging, dest);
    return { dest, backup };
  } catch (error) {
    rmSync(staging, { recursive: true, force: true });
    if (existsSync(backup) && !existsSync(dest)) renameSync(backup, dest);
    throw error;
  }
}

export function commitSkillCopy(transaction) {
  rmSync(transaction.backup, { recursive: true, force: true });
}

export function rollbackSkillCopy(transaction) {
  rmSync(transaction.dest, { recursive: true, force: true });
  if (existsSync(transaction.backup)) renameSync(transaction.backup, transaction.dest);
}

export function migrateLegacyFiles() {
  const paths = getMaestroPaths();
  mkdirSync(paths.home, { recursive: true });
  const migrated = [];

  if (!existsSync(paths.manifest) && existsSync(paths.legacyManifest)) {
    renameSync(paths.legacyManifest, paths.manifest);
    migrated.push("skills-manifest.json");
  }
  if (!existsSync(paths.exclude) && existsSync(paths.legacyExclude)) {
    renameSync(paths.legacyExclude, paths.exclude);
    migrated.push("maestro-exclude.txt");
  }

  const example = join(skillSourceDir(), "maestro-exclude.example.txt");
  if (!existsSync(paths.exclude) && existsSync(example)) {
    cpSync(example, paths.exclude);
    migrated.push("maestro-exclude.txt (from example)");
  }

  return migrated;
}

function normalizeInstallation(config) {
  if (!config || typeof config !== "object" || !Array.isArray(config.agents)) {
    throw new Error("Invalid Maestro setup installation record.");
  }
  const scope = config.scope === "project" ? "project" : "global";
  const projectRoot = scope === "project" && config.projectRoot
    ? resolve(String(config.projectRoot))
    : null;
  if (scope === "project" && !projectRoot) {
    throw new Error("Project installation record requires projectRoot.");
  }
  const agents = config.agents.map((agent) => {
    if (!agent || typeof agent !== "object" || Array.isArray(agent)) {
      throw new Error("Installation agents must be objects.");
    }
    const recordedPath = typeof agent.path === "string" && agent.path
      ? resolve(agent.path)
      : null;
    if (recordedPath && basename(recordedPath).toLowerCase() !== "maestro") {
      throw new Error(`Installation path must end in maestro: ${recordedPath}`);
    }
    const skillsPath = typeof agent.skillsPath === "string" && agent.skillsPath
      ? resolve(agent.skillsPath)
      : recordedPath && dirname(recordedPath);
    if (!skillsPath) throw new Error("Installation agent requires skillsPath or path.");
    const expectedPath = join(skillsPath, "maestro");
    if (recordedPath && pathIdentity(recordedPath) !== pathIdentity(expectedPath)) {
      throw new Error(`Installation path does not match skillsPath: ${recordedPath}`);
    }
    return {
      ...agent,
      id: String(agent.id || "unknown"),
      label: String(agent.label || agent.id || "Unknown agent"),
      skillsPath,
      path: expectedPath,
    };
  });
  return {
    ...config,
    version: undefined,
    scope,
    projectRoot,
    installedAt: config.installedAt || new Date().toISOString(),
    agents,
  };
}

function installationKey(installation) {
  return installation.scope === "project"
    ? `project:${pathIdentity(installation.projectRoot)}`
    : "global";
}

export function pathIdentity(path, platform = process.platform) {
  const normalized = resolve(path);
  return platform === "win32" ? normalized.toLowerCase() : normalized;
}

function normalizeRegistry(value) {
  if (!value || typeof value !== "object") {
    return { version: 2, installations: [] };
  }
  if (value.version === 2 && Array.isArray(value.installations)) {
    return {
      version: 2,
      installations: value.installations.map(normalizeInstallation),
    };
  }
  if (Array.isArray(value.agents)) {
    return { version: 2, installations: [normalizeInstallation(value)] };
  }
  throw new Error("Invalid Maestro setup registry.");
}

function writeJsonAtomic(path, value) {
  writeFileAtomic(path, `${JSON.stringify(value, null, 2)}\n`);
}

export function writeSetupRegistry(registry) {
  const { config: configPath } = getMaestroPaths();
  const normalized = normalizeRegistry(registry);
  writeJsonAtomic(configPath, normalized);
  return normalized;
}

export function saveSetupConfig(config) {
  const registry = loadSetupConfig() || { version: 2, installations: [] };
  const installation = normalizeInstallation(config);
  const key = installationKey(installation);
  registry.installations = registry.installations.filter(
    (item) => installationKey(item) !== key,
  );
  registry.installations.push(installation);
  return writeSetupRegistry(registry);
}

export function loadSetupConfig() {
  const { config: configPath } = getMaestroPaths();
  if (!existsSync(configPath)) return null;
  try {
    return normalizeRegistry(JSON.parse(readFileSync(configPath, "utf8")));
  } catch (error) {
    throw new Error(`Invalid Maestro setup registry at ${configPath}: ${error.message}`);
  }
}

export function removeSkillFrom(destDir) {
  const dest = join(destDir, "maestro");
  if (existsSync(dest)) {
    rmSync(dest, { recursive: true, force: true });
    return true;
  }
  return false;
}
