import assert from "node:assert/strict";
import { copyFileSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { test } from "node:test";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = resolve(__dirname, "..");
const REPO_ROOT = resolve(PACKAGE_ROOT, "..", "..");
const CLI = join(PACKAGE_ROOT, "bin", "cli.js");
const FIXTURE = join(REPO_ROOT, "tests", "fixtures", "sample-manifest.json");

function withManifest() {
  const home = mkdtempSync(join(tmpdir(), "maestro-cli-"));
  mkdirSync(home, { recursive: true });
  copyFileSync(FIXTURE, join(home, "skills-manifest.json"));
  return home;
}

function runCli(args, { home, input } = {}) {
  return spawnSync(process.execPath, [CLI, ...args], {
    cwd: REPO_ROOT,
    encoding: "utf8",
    input,
    env: { ...process.env, MAESTRO_HOME: home },
  });
}

test("route accepts an explicit domain through the public CLI", () => {
  const home = withManifest();
  try {
    const result = runCli(
      ["route", "--task", "fix CI", "--domain", "devops-git", "--json"],
      { home },
    );
    assert.equal(result.status, 0, result.stderr);
    const payload = JSON.parse(result.stdout);
    assert.equal(payload.results[0].domain, "devops-git");
  } finally {
    rmSync(home, { recursive: true, force: true });
  }
});

test("route accepts newline-delimited tasks on stdin", () => {
  const home = withManifest();
  try {
    const result = runCli(["route", "--json"], { home, input: "fix CI\n" });
    assert.equal(result.status, 0, result.stderr);
    const payload = JSON.parse(result.stdout);
    assert.equal(payload.task_count, 1);
  } finally {
    rmSync(home, { recursive: true, force: true });
  }
});

test("route bounds newline-delimited input", () => {
  const home = withManifest();
  try {
    const input = Array.from({ length: 101 }, (_, index) => `task ${index}`).join("\n");
    const result = runCli(["route", "--json"], { home, input });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /at most 100 tasks/);
    assert.doesNotMatch(result.stderr, /at .*cli\.js/);
  } finally {
    rmSync(home, { recursive: true, force: true });
  }
});

test("missing manifest produces remediation without a Python traceback", () => {
  const home = mkdtempSync(join(tmpdir(), "maestro-cli-empty-"));
  try {
    const result = runCli(["search", "fix CI", "--json"], { home });
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /maestro-skills manifest|manifest/i);
    assert.doesNotMatch(result.stderr, /Traceback/);
  } finally {
    rmSync(home, { recursive: true, force: true });
  }
});

test("malformed manifest entries fail closed without a Python traceback", () => {
  const home = mkdtempSync(join(tmpdir(), "maestro-cli-malformed-"));
  try {
    writeFileSync(
      join(home, "skills-manifest.json"),
      JSON.stringify({ version: 4, skills: [null] }),
      "utf8",
    );
    const result = runCli(["search", "fix CI", "--json"], { home });
    assert.equal(result.status, 2);
    assert.match(result.stderr, /skills\[0\]/);
    assert.doesNotMatch(result.stderr, /Traceback/);
  } finally {
    rmSync(home, { recursive: true, force: true });
  }
});

test("route also handles a missing manifest without a Python traceback", () => {
  const home = mkdtempSync(join(tmpdir(), "maestro-route-empty-"));
  try {
    const result = runCli(["route", "--task", "fix CI", "--json"], { home });
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /maestro-skills manifest|manifest/i);
    assert.doesNotMatch(result.stderr, /Traceback/);
  } finally {
    rmSync(home, { recursive: true, force: true });
  }
});

test("manifest reports local filesystem errors without a traceback", () => {
  const root = mkdtempSync(join(tmpdir(), "maestro-manifest-error-"));
  const home = join(root, "not-a-directory");
  try {
    writeFileSync(home, "occupied", "utf8");
    const result = runCli(["manifest", "--project-root", REPO_ROOT], { home });
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /error|not a directory|cannot/i);
    assert.doesNotMatch(result.stderr, /Traceback/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("invalid local registry fails closed without a Node stack trace", () => {
  const home = mkdtempSync(join(tmpdir(), "maestro-registry-error-"));
  try {
    writeFileSync(
      join(home, "config.json"),
      JSON.stringify({ version: 2, installations: [{ scope: "project", agents: [] }] }),
      "utf8",
    );
    const result = runCli(["remove", "-y"], { home });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /projectRoot|registry/i);
    assert.doesNotMatch(result.stderr, /at .*\.js:\d+/);
  } finally {
    rmSync(home, { recursive: true, force: true });
  }
});

test("search defaults to a compact human-readable result", () => {
  const home = withManifest();
  try {
    const result = runCli(["search", "fix CI"], { home });
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /Domain:/);
    assert.match(result.stdout, /gh-fix-ci/);
    assert.doesNotMatch(result.stdout, /^\s*\{/);
  } finally {
    rmSync(home, { recursive: true, force: true });
  }
});

test("search rejects unsafe result limits before invoking Python", () => {
  const result = runCli(["search", "fix CI", "--max-results", "100000"]);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /1 to 20/);
});

test("doctor is local-only and reports a missing manifest without a traceback", () => {
  const home = mkdtempSync(join(tmpdir(), "maestro-doctor-"));
  try {
    const result = runCli(["doctor", "--json"], { home });
    assert.equal(result.status, 1);
    const payload = JSON.parse(result.stdout);
    assert.equal(payload.network, "not-used");
    assert.equal(payload.checks.manifest.ok, false);
    assert.doesNotMatch(result.stderr, /Traceback/);
  } finally {
    rmSync(home, { recursive: true, force: true });
  }
});

test(
  "PowerShell fallback invokes the Python adapter correctly",
  { skip: process.platform !== "win32" },
  () => {
    const home = withManifest();
    try {
      const script = join(REPO_ROOT, "skills", "maestro", "scripts", "invoke.ps1");
      const result = spawnSync(
        "powershell",
        [
          "-NoProfile",
          "-File",
          script,
          "search",
          "fix CI",
          "--manifest",
          join(home, "skills-manifest.json"),
          "--json",
        ],
        { cwd: REPO_ROOT, encoding: "utf8" },
      );
      assert.equal(result.status, 0, result.stderr);
      assert.equal(JSON.parse(result.stdout).query, "fix CI");
    } finally {
      rmSync(home, { recursive: true, force: true });
    }
  },
);
