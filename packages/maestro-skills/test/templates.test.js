import assert from "node:assert/strict";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { test } from "node:test";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..", "..");

test(
  "template sync is dry-run by default and never deletes unrelated GitHub files",
  { skip: process.platform !== "win32" },
  () => {
    const target = mkdtempSync(join(tmpdir(), "maestro-templates-"));
    const unrelated = join(target, ".github", "workflows", "keep.yml");
    const conflict = join(target, ".github", "ISSUE_TEMPLATE", "bug_report.yml");
    try {
      mkdirSync(join(target, ".git"), { recursive: true });
      mkdirSync(dirname(unrelated), { recursive: true });
      mkdirSync(dirname(conflict), { recursive: true });
      writeFileSync(unrelated, "keep", "utf8");
      writeFileSync(conflict, "custom", "utf8");

      const script = join(REPO_ROOT, "scripts", "sync-templates.ps1");
      const dryRun = spawnSync(
        "powershell",
        ["-NoProfile", "-File", script, "-TargetRepo", target],
        { encoding: "utf8" },
      );
      assert.equal(dryRun.status, 0, dryRun.stderr);
      assert.equal(readFileSync(conflict, "utf8"), "custom");

      const apply = spawnSync(
        "powershell",
        ["-NoProfile", "-File", script, "-TargetRepo", target, "-Apply"],
        { encoding: "utf8" },
      );
      assert.equal(apply.status, 0, apply.stderr);
      assert.equal(readFileSync(conflict, "utf8"), "custom");
      assert.equal(readFileSync(unrelated, "utf8"), "keep");
      assert.equal(existsSync(join(target, ".github", "ISSUE_TEMPLATE", "chore.yml")), true);
    } finally {
      rmSync(target, { recursive: true, force: true });
    }
  },
);
