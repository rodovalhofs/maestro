import assert from "node:assert/strict";
import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { detectAgents } from "../lib/detect-agents.js";
import {
  copySkillTo,
  loadSetupConfig,
  pathIdentity,
  rollbackSkillCopy,
  saveSetupConfig,
  stageSkillCopy,
} from "../lib/install.js";
import { cleanMaestroHome, runRemove } from "../lib/remove.js";

test("global detection reports only agent homes that exist", () => {
  const home = mkdtempSync(join(tmpdir(), "maestro-agents-"));
  try {
    mkdirSync(join(home, ".codex"), { recursive: true });
    const agents = detectAgents({ project: false, home });
    const states = Object.fromEntries(agents.map((agent) => [agent.id, agent.detected]));
    assert.deepEqual(states, {
      cursor: false,
      claude: false,
      codex: true,
      universal: false,
    });
  } finally {
    rmSync(home, { recursive: true, force: true });
  }
});

test("remove deletes a Windows installation saved by setup", async () => {
  const root = mkdtempSync(join(tmpdir(), "maestro-remove-"));
  const previous = process.env.MAESTRO_HOME;
  process.env.MAESTRO_HOME = join(root, ".maestro");
  const skillsPath = join(root, ".codex", "skills");
  const installedPath = join(skillsPath, "maestro");
  try {
    mkdirSync(installedPath, { recursive: true });
    writeFileSync(join(installedPath, "SKILL.md"), "test", "utf8");
    saveSetupConfig({
      version: 1,
      agents: [{ id: "codex", label: "Codex", path: installedPath }],
    });

    await runRemove({ yes: true, all: false, cleanHome: false });

    assert.equal(existsSync(installedPath), false);
  } finally {
    process.env.MAESTRO_HOME = previous;
    rmSync(root, { recursive: true, force: true });
  }
});

test("clean home removes only Maestro-owned files", () => {
  const home = mkdtempSync(join(tmpdir(), "maestro-clean-"));
  try {
    writeFileSync(join(home, "skills-manifest.json"), "{}", "utf8");
    writeFileSync(join(home, "skill-runbooks.user.json"), "{}", "utf8");
    writeFileSync(join(home, "keep-me.txt"), "user data", "utf8");

    const removed = cleanMaestroHome(home);

    assert.deepEqual(
      removed.sort(),
      ["skill-runbooks.user.json", "skills-manifest.json"].sort(),
    );
    assert.equal(existsSync(join(home, "keep-me.txt")), true);
  } finally {
    rmSync(home, { recursive: true, force: true });
  }
});

test("setup registry preserves installations from multiple projects", () => {
  const root = mkdtempSync(join(tmpdir(), "maestro-registry-"));
  const previous = process.env.MAESTRO_HOME;
  process.env.MAESTRO_HOME = join(root, ".maestro");
  try {
    saveSetupConfig({
      scope: "project",
      projectRoot: join(root, "project-a"),
      installedAt: "2026-01-01T00:00:00Z",
      agents: [{ id: "codex", skillsPath: join(root, "project-a", ".codex", "skills") }],
    });
    saveSetupConfig({
      scope: "project",
      projectRoot: join(root, "project-b"),
      installedAt: "2026-01-02T00:00:00Z",
      agents: [{ id: "codex", skillsPath: join(root, "project-b", ".codex", "skills") }],
    });

    const registry = loadSetupConfig();
    assert.equal(registry.version, 2);
    assert.equal(registry.installations.length, 2);
  } finally {
    process.env.MAESTRO_HOME = previous;
    rmSync(root, { recursive: true, force: true });
  }
});

test("project removal does not touch another project's installation", async () => {
  const root = mkdtempSync(join(tmpdir(), "maestro-project-remove-"));
  const previous = process.env.MAESTRO_HOME;
  process.env.MAESTRO_HOME = join(root, ".maestro");
  const projectA = join(root, "project-a");
  const projectB = join(root, "project-b");
  const skillsA = join(projectA, ".codex", "skills");
  const skillsB = join(projectB, ".codex", "skills");
  try {
    for (const path of [skillsA, skillsB]) {
      mkdirSync(join(path, "maestro"), { recursive: true });
      writeFileSync(join(path, "maestro", "SKILL.md"), "test", "utf8");
    }
    saveSetupConfig({
      scope: "project",
      projectRoot: projectA,
      agents: [{ id: "codex", label: "Codex A", skillsPath: skillsA }],
    });
    saveSetupConfig({
      scope: "project",
      projectRoot: projectB,
      agents: [{ id: "codex", label: "Codex B", skillsPath: skillsB }],
    });

    await runRemove({ yes: true, project: projectA, all: false, cleanHome: false });

    assert.equal(existsSync(join(skillsA, "maestro")), false);
    assert.equal(existsSync(join(skillsB, "maestro")), true);
  } finally {
    process.env.MAESTRO_HOME = previous;
    rmSync(root, { recursive: true, force: true });
  }
});

test("skill copy replaces an existing install without leaving staging directories", () => {
  const root = mkdtempSync(join(tmpdir(), "maestro-atomic-copy-"));
  const skillsPath = join(root, "skills");
  const existing = join(skillsPath, "maestro");
  try {
    mkdirSync(existing, { recursive: true });
    writeFileSync(join(existing, "old.txt"), "old", "utf8");

    copySkillTo(skillsPath);

    assert.equal(existsSync(join(existing, "SKILL.md")), true);
    assert.equal(existsSync(join(existing, "old.txt")), false);
    assert.deepEqual(
      readdirSync(skillsPath).filter((name) => name.startsWith(".maestro-")),
      [],
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("registry rejects inconsistent install paths before removal can use them", () => {
  const root = mkdtempSync(join(tmpdir(), "maestro-registry-path-"));
  const previous = process.env.MAESTRO_HOME;
  process.env.MAESTRO_HOME = join(root, ".maestro");
  try {
    mkdirSync(process.env.MAESTRO_HOME, { recursive: true });
    writeFileSync(
      join(process.env.MAESTRO_HOME, "config.json"),
      JSON.stringify({
        version: 2,
        installations: [{
          scope: "global",
          agents: [{
            id: "codex",
            skillsPath: join(root, ".codex", "skills"),
            path: join(root, "unrelated", "maestro"),
          }],
        }],
      }),
      "utf8",
    );

    assert.throws(() => loadSetupConfig(), /does not match skillsPath/);
  } finally {
    process.env.MAESTRO_HOME = previous;
    rmSync(root, { recursive: true, force: true });
  }
});

test("path identity preserves case on case-sensitive platforms", () => {
  assert.notEqual(pathIdentity("/repo/A", "linux"), pathIdentity("/repo/a", "linux"));
  assert.equal(
    pathIdentity("C:\\Repo\\A", "win32"),
    pathIdentity("c:\\repo\\a", "win32"),
  );
});

test("staged skill copy can restore the previous installation", () => {
  const root = mkdtempSync(join(tmpdir(), "maestro-copy-rollback-"));
  const skillsPath = join(root, "skills");
  const installed = join(skillsPath, "maestro");
  try {
    mkdirSync(installed, { recursive: true });
    writeFileSync(join(installed, "old.txt"), "previous", "utf8");

    const transaction = stageSkillCopy(skillsPath);
    assert.equal(existsSync(join(installed, "SKILL.md")), true);
    rollbackSkillCopy(transaction);

    assert.equal(existsSync(join(installed, "old.txt")), true);
    assert.equal(existsSync(join(installed, "SKILL.md")), false);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
