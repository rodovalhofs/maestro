import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { test } from "node:test";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = resolve(__dirname, "..");
const REPO_ROOT = resolve(PACKAGE_ROOT, "..", "..");
const SCOPED_ROOT = join(REPO_ROOT, "packages", "rodovalhofs-maestro");

function packageJson(path) {
  return JSON.parse(readFileSync(join(path, "package.json"), "utf8"));
}

function cli(path, ...args) {
  return spawnSync(process.execPath, [join(path, "bin", "cli.js"), ...args], {
    encoding: "utf8",
    cwd: REPO_ROOT,
  });
}

test("both npm adapters expose the same version and command surface", () => {
  const root = packageJson(REPO_ROOT);
  const main = packageJson(PACKAGE_ROOT);
  const scoped = packageJson(SCOPED_ROOT);
  assert.equal(root.version, main.version);
  assert.equal(scoped.version, main.version);

  const mainVersion = cli(PACKAGE_ROOT, "--version");
  const scopedVersion = cli(SCOPED_ROOT, "--version");
  assert.equal(mainVersion.status, 0, mainVersion.stderr);
  assert.equal(scopedVersion.status, 0, scopedVersion.stderr);
  assert.equal(mainVersion.stdout.trim(), main.version);
  assert.equal(scopedVersion.stdout.trim(), main.version);

  const requiredCommands = ["setup", "remove", "search", "route", "manifest", "doctor", "runbook"];
  const mainHelp = cli(PACKAGE_ROOT, "--help").stdout;
  const scopedHelp = cli(SCOPED_ROOT, "--help").stdout;
  for (const command of requiredCommands) {
    assert.match(mainHelp, new RegExp(`\\b${command}\\b`));
    assert.match(scopedHelp, new RegExp(`\\b${command}\\b`));
  }
});

test("scoped npm adapter ships user-facing documentation", () => {
  assert.equal(existsSync(join(SCOPED_ROOT, "README.md")), true);
});

test("package archive verification targets both public package directories", () => {
  const result = spawnSync(process.execPath, [join(REPO_ROOT, "scripts", "verify-packages.mjs")], {
    encoding: "utf8",
    cwd: REPO_ROOT,
  });
  assert.equal(result.status, 0, result.stderr || result.stdout);
  assert.match(result.stdout, /maestro-skills@0\.2\.0/);
  assert.match(result.stdout, /@rodovalhofs\/maestro@0\.2\.0/);
  assert.doesNotMatch(result.stdout, /maestro-monorepo/);
});
