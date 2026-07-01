import { cpSync, existsSync, mkdirSync, readFileSync, renameSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { getMaestroPaths, skillSourceDir } from "./paths.js";

export function copySkillTo(destDir) {
  const src = skillSourceDir();
  const dest = join(destDir, "maestro");
  rmSync(dest, { recursive: true, force: true });
  mkdirSync(dirname(dest), { recursive: true });
  cpSync(src, dest, { recursive: true });
  const pycache = join(dest, "scripts", "__pycache__");
  if (existsSync(pycache)) rmSync(pycache, { recursive: true, force: true });
  return dest;
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

export function saveSetupConfig(config) {
  const { config: configPath } = getMaestroPaths();
  mkdirSync(dirname(configPath), { recursive: true });
  writeFileSync(configPath, JSON.stringify(config, null, 2), "utf8");
}

export function loadSetupConfig() {
  const { config: configPath } = getMaestroPaths();
  if (!existsSync(configPath)) return null;
  return JSON.parse(readFileSync(configPath, "utf8"));
}

export function removeSkillFrom(destDir) {
  const dest = join(destDir, "maestro");
  if (existsSync(dest)) {
    rmSync(dest, { recursive: true, force: true });
    return true;
  }
  return false;
}
