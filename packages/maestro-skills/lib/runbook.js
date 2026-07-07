import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { getMaestroPaths } from "./paths.js";

const USER_RUNBOOKS = () => join(getMaestroPaths().home, "skill-runbooks.user.json");

function emptyUserRunbooks() {
  return { version: 1, skills: {} };
}

export function loadUserRunbooks() {
  const path = USER_RUNBOOKS();
  if (!existsSync(path)) return { path, data: emptyUserRunbooks() };
  try {
    const data = JSON.parse(readFileSync(path, "utf8"));
    if (!data.skills || typeof data.skills !== "object") data.skills = {};
    return { path, data };
  } catch {
    return { path, data: emptyUserRunbooks() };
  }
}

export function saveUserRunbooks(data) {
  const path = USER_RUNBOOKS();
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, JSON.stringify(data, null, 2) + "\n", "utf8");
  return path;
}

export function listRunbooks() {
  const { path, data } = loadUserRunbooks();
  const names = Object.keys(data.skills).filter((n) => !n.startsWith("_"));
  return { path, names, skills: data.skills };
}

export function addRunbook(name, { summary = "", notes = "" } = {}) {
  if (!name || name.startsWith("_")) {
    throw new Error("Skill name is required and must not start with _");
  }
  const { data } = loadUserRunbooks();
  if (data.skills[name]) {
    throw new Error(`Runbook already exists for "${name}". Use: maestro-skills runbook edit ${name}`);
  }
  data.skills[name] = {
    summary: summary || `Custom runbook for ${name}`,
    graph_hint: notes || "Add preflight steps as needed.",
    preflight: [],
  };
  const path = saveUserRunbooks(data);
  return { path, skill: data.skills[name] };
}

export function editRunbookHint(name) {
  const { path } = loadUserRunbooks();
  return {
    path,
    hint: `Edit ${path} — add or update skills.${name}.preflight[]`,
    example: {
      id: "my-step",
      label: "Human-readable step",
      command: "npm",
      args: ["run", "lint"],
      notes: "Run from project root",
    },
  };
}

export function discoverAllowlistPath() {
  return join(getMaestroPaths().home, "discover-allowlist.txt");
}

export function discoverAllowlistExample() {
  return [
    "# One GitHub repo per line (owner/repo or owner/repo@skill)",
    "# Only listed repos may be auto-installed when you explicitly allow it.",
    "# Example:",
    "# rodovalhofs/maestro",
    "",
  ].join("\n");
}
