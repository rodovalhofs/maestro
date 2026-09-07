#!/usr/bin/env node
// Exercise the actual tarballs outside the checkout, including dependency resolution.
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const records = JSON.parse(readFileSync(join(ROOT, "artifacts/release/release.json"), "utf8"));
const output = [];
for (const record of records) {
  const temp = mkdtempSync(join(tmpdir(), "maestro-release-smoke-"));
  try {
    const archive = join(ROOT, "artifacts/release", record.filename).replaceAll("\\", "/");
    writeFileSync(join(temp, "package.json"), JSON.stringify({ name: "release-smoke", private: true,
      dependencies: { [record.name]: `file:${archive}` } }));
    const install = process.platform === "win32"
      ? spawnSync(process.env.ComSpec || "cmd.exe", ["/d", "/s", "/c", "npm install --ignore-scripts --no-audit --no-fund"], { cwd: temp, encoding: "utf8", shell: false })
      : spawnSync("npm", ["install", "--ignore-scripts", "--no-audit", "--no-fund"], { cwd: temp, encoding: "utf8", shell: false });
    if (install.status !== 0) throw new Error(install.stderr || "Archive install failed");
    const project = join(temp, "project");
    mkdirSync(project);
    const cli = join(temp, "node_modules", ...record.name.split("/"), "bin/cli.js");
    const env = { ...process.env, MAESTRO_HOME: join(temp, "state") };
    const run = (...args) => {
      const result = spawnSync(process.execPath, [cli, ...args], { cwd: project, env, encoding: "utf8", shell: false });
      if (result.status !== 0) throw new Error(result.stderr || result.stdout);
      return result.stdout;
    };
    if (run("--version").trim() !== record.version) throw new Error("Installed version mismatch");
    run("setup", "--project", "--universal", "-y");
    const paths = ["maestro", "maestro-prompt-designer"].map((name) => join(project, ".agents/skills", name, "SKILL.md"));
    if (!paths.every(existsSync)) throw new Error("Incomplete installed bundle");
    run("setup", "--project", "--universal", "-y");
    if (!JSON.parse(run("doctor", "--json")).ok) throw new Error("Installed doctor failed");
    const search = JSON.parse(run("search", "consolidate approved task specification", "--local-only", "--json"));
    if (!search.results.some((skill) => skill.name === "maestro-prompt-designer")) throw new Error("Designer not discoverable");
    if (search.selection.stage !== "retrieval_only") throw new Error("Stale search engine");
    run("route", "--task", "design UI", "--local-only", "--json");
    run("remove", "--project", project, "-y");
    if (paths.some(existsSync)) throw new Error("Bundle removal incomplete");
    output.push({ name: record.name, version: record.version, passed: true,
      checks: ["archive_install", "version", "bundle_setup", "upgrade", "doctor", "search", "route", "remove"] });
    console.log(`${record.name}@${record.version}: isolated archive install, upgrade, search, route, doctor and removal passed`);
  } finally {
    if (temp.startsWith(join(tmpdir(), "maestro-release-smoke-"))) rmSync(temp, { recursive: true, force: true });
  }
}
mkdirSync(join(ROOT, "artifacts/validation"), { recursive: true });
writeFileSync(join(ROOT, "artifacts/validation/release-smoke.json"), `${JSON.stringify(output, null, 2)}\n`);
