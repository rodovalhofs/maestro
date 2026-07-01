#!/usr/bin/env node
/**
 * Copy canonical skill + shared lib to publishable npm packages.
 * Usage: node scripts/sync-skill-to-cli.mjs [--target maestro-skills|rodovalhofs-maestro|all]
 */
import { cpSync, existsSync, mkdirSync, readdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");
const SOURCE_SKILL = join(ROOT, "skills", "maestro");
const PACKAGES = {
  "maestro-skills": join(ROOT, "packages", "maestro-skills"),
  "rodovalhofs-maestro": join(ROOT, "packages", "rodovalhofs-maestro"),
};

function copyDir(src, dest) {
  if (!existsSync(src)) {
    throw new Error(`Source not found: ${src}`);
  }
  rmSync(dest, { recursive: true, force: true });
  cpSync(src, dest, { recursive: true });
  for (const dir of ["__pycache__", "node_modules"]) {
    const nested = join(dest, "scripts", dir);
    if (existsSync(nested)) rmSync(nested, { recursive: true, force: true });
  }
}

function copySharedLib(targetPkg) {
  const libSrc = join(PACKAGES["maestro-skills"], "lib");
  const libDest = join(targetPkg, "lib");
  if (targetPkg === PACKAGES["maestro-skills"]) return;
  rmSync(libDest, { recursive: true, force: true });
  cpSync(libSrc, libDest, { recursive: true });
  cpSync(join(PACKAGES["maestro-skills"], "agents.json"), join(targetPkg, "agents.json"));
}

function syncPackage(name) {
  const pkgDir = PACKAGES[name];
  if (!pkgDir) throw new Error(`Unknown package: ${name}`);
  mkdirSync(pkgDir, { recursive: true });
  copyDir(SOURCE_SKILL, join(pkgDir, "skill"));
  if (name !== "maestro-skills") {
    copySharedLib(pkgDir);
    writeScopedCli(pkgDir);
  }
  console.log(`Synced skill → ${name}`);
}

function writeScopedCli(pkgDir) {
  const binPath = join(pkgDir, "bin", "cli.js");
  mkdirSync(join(pkgDir, "bin"), { recursive: true });
  const content = `#!/usr/bin/env node
import { Command } from "commander";
import { runRemove } from "../lib/remove.js";
import { runSetup } from "../lib/setup.js";

const program = new Command();
program.name("maestro").description("Maestro skill orchestrator (@rodovalhofs/maestro)").version("0.1.0");
program.command("setup").description("Interactive setup").option("--project").option("--cursor").option("--claude").option("--codex").option("--universal").option("-y, --yes").option("--no-skills-registry").action(runSetup);
program.command("remove").description("Remove Maestro").option("-y, --yes").option("--all").option("--clean-home").action(runRemove);
program.parseAsync(process.argv);
`;
  writeFileSync(binPath, content, "utf8");
}

const arg = process.argv.find((a) => a.startsWith("--target"));
const target = arg ? arg.split("=")[1] || process.argv[process.argv.indexOf(arg) + 1] : "all";

if (target === "all") {
  for (const name of Object.keys(PACKAGES)) syncPackage(name);
} else {
  syncPackage(target);
}
