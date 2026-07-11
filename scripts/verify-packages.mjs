#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const packages = [
  { directory: "maestro-skills", name: "maestro-skills" },
  { directory: "rodovalhofs-maestro", name: "@rodovalhofs/maestro" },
];
const required = ["bin/cli.js", "lib/cli.js", "skill/SKILL.md", "package.json", "README.md"];

for (const item of packages) {
  const cwd = join(ROOT, "packages", item.directory);
  const result = process.platform === "win32"
    ? spawnSync(
        process.env.ComSpec || "cmd.exe",
        ["/d", "/s", "/c", "npm pack --dry-run --json --ignore-scripts"],
        { cwd, encoding: "utf8", shell: false },
      )
    : spawnSync(
        "npm",
        ["pack", "--dry-run", "--json", "--ignore-scripts"],
        { cwd, encoding: "utf8", shell: false },
      );
  if (result.status !== 0) {
    process.stderr.write(result.stderr || result.stdout || result.error?.message || "npm pack failed\n");
    process.exit(result.status ?? 1);
  }
  const payload = JSON.parse(result.stdout);
  const archive = payload[0];
  if (archive?.name !== item.name) {
    throw new Error(`Expected package ${item.name}, got ${archive?.name || "unknown"}`);
  }
  const files = new Set((archive.files || []).map((file) => file.path));
  const missing = required.filter((path) => !files.has(path));
  if (missing.length) {
    throw new Error(`${item.name} archive is missing: ${missing.join(", ")}`);
  }
  console.log(`${archive.name}@${archive.version}: ${archive.files.length} files, ${archive.size} bytes`);
}
