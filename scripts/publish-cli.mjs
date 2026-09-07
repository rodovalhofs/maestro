#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { pythonCommand } from "../packages/maestro-skills/lib/python.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const targets = { "maestro-skills": "maestro-skills", "rodovalhofs-maestro": "@rodovalhofs/maestro" };
const target = process.argv[2] || "maestro-skills";
if (target !== "all" && !Object.hasOwn(targets, target)) throw new Error(`Unknown target: ${target}`);
const py = pythonCommand();
if (!py) throw new Error("Python 3.10+ required");

function check(command, args, cwd = ROOT) {
  const result = spawnSync(command, args, { cwd, stdio: "inherit", shell: false });
  if (result.status !== 0) process.exit(result.status ?? 1);
}

// --prepared reuses archives already inspected in this release session. It does
// not rebuild them, so publication uses the exact bytes reviewed by the maintainer.
if (!process.argv.includes("--prepared")) {
  check(process.execPath, [join(ROOT, "scripts/sync-skill-to-cli.mjs")]);
  check(py[0], [...py.slice(1), "-m", "unittest", "discover", "-s", "tests", "-q"]);
  check(process.execPath, ["--test"], join(ROOT, "packages/maestro-skills"));
  check(process.execPath, [join(ROOT, "scripts/verify-packages.mjs"), "--keep"]);
}

const output = join(ROOT, "artifacts/release");
const records = JSON.parse(readFileSync(join(output, "release.json"), "utf8"));
const version = JSON.parse(readFileSync(join(ROOT, "package.json"), "utf8")).version;
let failed = false;
for (const name of target === "all" ? Object.values(targets) : [targets[target]]) {
  const record = records.find((item) => item.name === name && item.version === version);
  if (!record || !/^[a-z0-9.-]+\.tgz$/.test(record.filename)) throw new Error(`Missing reviewed archive: ${name}`);
  const archive = join(output, record.filename);
  const integrity = `sha512-${createHash("sha512").update(readFileSync(archive)).digest("base64")}`;
  if (integrity !== record.integrity) throw new Error(`Archive changed after review: ${name}`);
  check(py[0], [...py.slice(1), join(ROOT, "scripts/verify-archive.py"), archive,
    "--expected", join(output, "expected-files.json")]);
  const result = process.platform === "win32"
    ? spawnSync(process.env.ComSpec || "cmd.exe", ["/d", "/s", "/c",
        `npm publish ${record.filename} --access public --ignore-scripts`],
      { cwd: output, stdio: "inherit", shell: false })
    : spawnSync("npm", ["publish", record.filename, "--access", "public", "--ignore-scripts"],
      { cwd: output, stdio: "inherit", shell: false });
  if (result.status !== 0) failed = true;
}
process.exitCode = failed ? 1 : 0;
