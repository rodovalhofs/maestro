import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, statSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { stageSkillBundle } from "../lib/install.js";

const CLI = resolve(dirname(fileURLToPath(import.meta.url)), "../bin/cli.js");

test("public CLI installs, upgrades, diagnoses and removes both skills in one project", () => {
  const root = mkdtempSync(join(tmpdir(), "maestro-bundle-"));
  const skills = join(root, ".agents", "skills");
  const env = { ...process.env, MAESTRO_HOME: join(root, "state") };
  const run = (...args) => {
    const result = spawnSync(process.execPath, [CLI, ...args], { cwd: root, env, encoding: "utf8" });
    assert.equal(result.status, 0, result.stderr || result.stdout);
    return result.stdout;
  };
  try {
    mkdirSync(join(skills, "unrelated"), { recursive: true });
    writeFileSync(join(skills, "unrelated", "SKILL.md"), "keep");
    for (const name of ["maestro", "maestro-prompt-designer"]) {
      mkdirSync(join(skills, name), { recursive: true });
      writeFileSync(join(skills, name, "SKILL.md"), "old installation");
    }
    run("setup", "--project", "--universal", "-y");
    for (const name of ["maestro", "maestro-prompt-designer"]) {
      assert.match(readFileSync(join(skills, name, "SKILL.md"), "utf8"), /^---/);
    }
    run("setup", "--project", "--universal", "-y");
    const health = JSON.parse(run("doctor", "--json"));
    assert.equal(health.ok, true);
    const payload = JSON.parse(run("route", "--task", "consolidate task specification", "--local-only", "--json"));
    // Windows may expose the same directory through its long or 8.3 name.
    const actualRoot = statSync(payload.results[0].catalog.active_project_root, { bigint: true });
    const expectedRoot = statSync(root, { bigint: true });
    assert.deepEqual([actualRoot.dev, actualRoot.ino], [expectedRoot.dev, expectedRoot.ino]);
    assert.equal(payload.results[0].discover.enabled, false);
    assert.ok(payload.results[0].results.some((skill) => skill.name === "maestro-prompt-designer"));
    run("remove", "--project", root, "-y");
    assert.equal(existsSync(join(skills, "maestro")), false);
    assert.equal(existsSync(join(skills, "maestro-prompt-designer")), false);
    assert.equal(readFileSync(join(skills, "unrelated", "SKILL.md"), "utf8"), "keep");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("bundle failure restores the first skill and preserves an occupied second destination", () => {
  const root = mkdtempSync(join(tmpdir(), "maestro-bundle-failure-"));
  try {
    mkdirSync(join(root, "maestro"));
    writeFileSync(join(root, "maestro", "SKILL.md"), "old");
    writeFileSync(join(root, "maestro-prompt-designer"), "occupied file");
    assert.throws(() => stageSkillBundle(root));
    assert.equal(readFileSync(join(root, "maestro", "SKILL.md"), "utf8"), "old");
    assert.equal(readFileSync(join(root, "maestro-prompt-designer"), "utf8"), "occupied file");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
