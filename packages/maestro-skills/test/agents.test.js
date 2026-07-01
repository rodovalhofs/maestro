import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import assert from "node:assert/strict";

const __dirname = dirname(fileURLToPath(import.meta.url));
const agents = JSON.parse(
  readFileSync(join(__dirname, "..", "agents.json"), "utf8"),
).agents;

test("agents.json includes codex", () => {
  const codex = agents.find((a) => a.id === "codex");
  assert.ok(codex);
  assert.equal(codex.globalSkillsDir, ".codex/skills");
  assert.equal(codex.skillsCliAgent, "codex");
});
