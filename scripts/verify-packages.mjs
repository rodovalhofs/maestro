#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { pythonCommand } from "../packages/maestro-skills/lib/python.js";
import { RELEASE_FILES } from "./release-layout.mjs";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const version = JSON.parse(readFileSync(join(ROOT, "package.json"))).version;
const packages = [
  { directory: "maestro-skills", name: "maestro-skills" },
  { directory: "rodovalhofs-maestro", name: "@rodovalhofs/maestro" },
];
const keep = process.argv.includes("--keep");
const output = keep ? join(ROOT, "artifacts", "release") : mkdtempSync(join(tmpdir(), "maestro-pack-"));
mkdirSync(output, { recursive: true });
const expected = join(output, "expected-files.json");
writeFileSync(expected, JSON.stringify(RELEASE_FILES));
const py = pythonCommand();
if (!py) throw new Error("Python 3.10+ required for archive inspection");
const records = [];
try {
  for (const item of packages) {
    const cwd = join(ROOT, "packages", item.directory);
    const args = ["pack", "--json", "--ignore-scripts"];
    const options = { cwd, encoding: "utf8", shell: false,
      env: { ...process.env, npm_config_pack_destination: output } };
    const result = process.platform === "win32"
      ? spawnSync(process.env.ComSpec || "cmd.exe", ["/d", "/s", "/c",
          "npm pack --json --ignore-scripts"], options)
      : spawnSync("npm", args, options);
    if (result.status !== 0) throw new Error(result.stderr || result.error?.message || "npm pack failed");
    const archive = JSON.parse(result.stdout)[0];
    if (archive.name !== item.name || archive.version !== version) throw new Error("Package identity/version mismatch");
    const actual = archive.files.map((file) => file.path).sort();
    if (JSON.stringify(actual) !== JSON.stringify(RELEASE_FILES)) throw new Error(`Unexpected release inventory: ${item.name}`);
    const path = join(output, archive.filename);
    const inspection = spawnSync(py[0], [...py.slice(1), join(ROOT, "scripts", "verify-archive.py"), path, "--expected", expected], { encoding: "utf8" });
    if (inspection.status !== 0) throw new Error(inspection.stderr || "Archive inspection failed");
    const integrity = `sha512-${createHash("sha512").update(readFileSync(path)).digest("base64")}`;
    if (integrity !== archive.integrity) throw new Error("Archive integrity mismatch");
    records.push({ name: item.name, version, filename: archive.filename, integrity, files: actual.length });
    console.log(`${item.name}@${version}: ${actual.length} reviewed files, actual tar contents and integrity verified`);
  }
  if (keep) writeFileSync(join(output, "release.json"), `${JSON.stringify(records, null, 2)}\n`);
} finally {
  // output is an explicitly created temporary directory, never a user-supplied path.
  if (!keep && output.startsWith(join(tmpdir(), "maestro-pack-"))) rmSync(output, { recursive: true, force: true });
}
