import { existsSync, readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import assert from "node:assert/strict";
import { bundledBuildManifest, bundledRunbooksJson, skillSourceDir } from "../lib/paths.js";
import {
  addRunbook,
  discoverAllowlistExample,
  listRunbooks,
  loadUserRunbooks,
} from "../lib/runbook.js";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PKG_ROOT = join(__dirname, "..");

test("skillSourceDir resolves bundled skill with SKILL.md", () => {
  const src = skillSourceDir();
  assert.ok(existsSync(join(src, "SKILL.md")));
  assert.equal(src, join(PKG_ROOT, "skill"));
});

test("bundledBuildManifest points to build_manifest.py", () => {
  const script = bundledBuildManifest();
  assert.ok(existsSync(script));
  assert.ok(script.endsWith("build_manifest.py"));
});

test("bundledRunbooksJson exists after sync", () => {
  const path = bundledRunbooksJson();
  assert.ok(existsSync(path));
});

test("runbook add/list roundtrip in temp home", () => {
  const prev = process.env.MAESTRO_HOME;
  const tmp = join(homedir(), ".maestro-test-" + process.pid);
  process.env.MAESTRO_HOME = tmp;
  mkdirSync(tmp, { recursive: true });
  try {
    addRunbook("test-skill", { summary: "s", notes: "n" });
    const { names } = listRunbooks();
    assert.ok(names.includes("test-skill"));
  } finally {
    process.env.MAESTRO_HOME = prev;
    rmSync(tmp, { recursive: true, force: true });
  }
});

test("malformed user runbook fails closed and is not overwritten", () => {
  const prev = process.env.MAESTRO_HOME;
  const tmp = join(homedir(), ".maestro-test-malformed-" + process.pid);
  process.env.MAESTRO_HOME = tmp;
  mkdirSync(tmp, { recursive: true });
  const path = join(tmp, "skill-runbooks.user.json");
  const malformed = "{broken";
  writeFileSync(path, malformed, "utf8");
  try {
    assert.throws(() => loadUserRunbooks(), /invalid json/i);
    assert.throws(() => addRunbook("safe-skill"), /invalid json/i);
    assert.equal(readFileSync(path, "utf8"), malformed);
  } finally {
    process.env.MAESTRO_HOME = prev;
    rmSync(tmp, { recursive: true, force: true });
  }
});

test("allowlist template states that installs remain manual", () => {
  const example = discoverAllowlistExample();
  assert.match(example, /never auto-installs/i);
  assert.doesNotMatch(example, /may be auto-installed/i);
});
