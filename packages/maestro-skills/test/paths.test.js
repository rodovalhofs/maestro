import { existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import assert from "node:assert/strict";
import { bundledBuildManifest, skillSourceDir } from "../lib/paths.js";

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
