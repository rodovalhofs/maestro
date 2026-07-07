import { existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import assert from "node:assert/strict";
import { bundledBuildManifest, bundledRunbooksJson, skillSourceDir } from "../lib/paths.js";
import { addRunbook, listRunbooks } from "../lib/runbook.js";
import { mkdirSync, rmSync } from "node:fs";
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
