#!/usr/bin/env node
import { copyFileSync, existsSync, lstatSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { CLI_FILES, PACKAGED_DIRS, RELEASE_FILES, SKILL_FILES } from "./release-layout.mjs";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const NAMES = ["maestro-skills", "rodovalhofs-maestro"];
const flag = process.argv.findIndex((arg) => arg === "--target" || arg.startsWith("--target="));
const target = flag < 0 ? "all" : process.argv[flag].split("=")[1] || process.argv[flag + 1];
if (target !== "all" && !NAMES.includes(target)) throw new Error(`Unknown target: ${target}`);

function inside(root, path) {
  const rel = relative(root, resolve(path));
  if (!rel || rel === ".." || rel.startsWith(`..${sep}`) || resolve(root, rel) !== resolve(path)) {
    throw new Error(`Unsafe release path: ${path}`);
  }
  for (let current = resolve(path); current !== resolve(root); current = dirname(current)) {
    if (existsSync(current) && lstatSync(current).isSymbolicLink()) throw new Error(`Release symlink: ${current}`);
  }
}

function copy(src, dest) {
  inside(ROOT, src);
  inside(ROOT, dest);
  if (!lstatSync(src).isFile()) throw new Error(`Not a regular release input: ${src}`);
  mkdirSync(dirname(dest), { recursive: true });
  copyFileSync(src, dest);
}

for (const name of target === "all" ? NAMES : [target]) {
  const pkg = join(ROOT, "packages", name);
  inside(ROOT, pkg);
  for (const [skill, files] of Object.entries(SKILL_FILES)) {
    const dest = join(pkg, PACKAGED_DIRS[skill]);
    inside(pkg, dest);
    rmSync(dest, { recursive: true, force: true });
    for (const file of files) copy(join(ROOT, "skills", skill, file), join(dest, file));
  }
  if (name !== "maestro-skills") {
    for (const file of CLI_FILES.filter((file) => file !== "bin/cli.js")) {
      copy(join(ROOT, "packages", "maestro-skills", file), join(pkg, file));
    }
  }
  copy(join(ROOT, "LICENSE"), join(pkg, "LICENSE"));
  const jsonPath = join(pkg, "package.json");
  const json = JSON.parse(readFileSync(jsonPath, "utf8"));
  json.files = RELEASE_FILES.filter((file) => file !== "package.json");
  writeFileSync(jsonPath, `${JSON.stringify(json, null, 2)}\n`, "utf8");
  console.log(`Synced reviewed Maestro + Prompt Designer files to ${name}`);
}
