import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { loadSetupConfig } from "./install.js";
import { getMaestroPaths, packageVersion, skillSourceDir } from "./paths.js";
import { pythonCommand } from "./python.js";
import { loadUserRunbooks } from "./runbook.js";

const SUPPORTED_MANIFEST_VERSIONS = new Set([2, 3, 4]);

export function runDoctorChecks() {
  const paths = getMaestroPaths();
  const checks = {};

  const python = pythonCommand();
  checks.python = python
    ? { ok: true, command: python.join(" ") }
    : { ok: false, message: "Python 3 is unavailable." };

  try {
    const source = skillSourceDir();
    checks.skill = { ok: true, path: source };
  } catch (error) {
    checks.skill = { ok: false, message: String(error.message || error) };
  }

  if (!existsSync(paths.manifest)) {
    checks.manifest = {
      ok: false,
      path: paths.manifest,
      message: "Manifest missing. Run: maestro-skills manifest --project-root .",
    };
  } else {
    try {
      const manifest = JSON.parse(readFileSync(paths.manifest, "utf8"));
      if (!Array.isArray(manifest.skills)) throw new Error("field 'skills' must be an array");
      if (!SUPPORTED_MANIFEST_VERSIONS.has(manifest.version)) {
        throw new Error(`unsupported version ${JSON.stringify(manifest.version)}`);
      }
      manifest.skills.forEach((skill, index) => {
        if (!skill || typeof skill !== "object" || Array.isArray(skill)) {
          throw new Error(`skills[${index}] must be an object`);
        }
        for (const field of ["name", "path"]) {
          if (typeof skill[field] !== "string" || !skill[field].trim()) {
            throw new Error(`skills[${index}].${field} must be a non-empty string`);
          }
        }
      });
      checks.manifest = {
        ok: true,
        path: paths.manifest,
        version: manifest.version,
        skills: manifest.skills.length,
      };
    } catch (error) {
      checks.manifest = {
        ok: false,
        path: paths.manifest,
        message: `Invalid manifest: ${error.message || error}`,
      };
    }
  }

  try {
    const registry = loadSetupConfig();
    const installations = registry?.installations || [];
    const agents = installations.flatMap((item) => item.agents);
    const stale = agents.filter((agent) => {
      const skillPath = agent.path || (agent.skillsPath && join(agent.skillsPath, "maestro"));
      return !skillPath || !existsSync(skillPath);
    });
    checks.installations = {
      ok: stale.length === 0,
      registered: installations.length,
      agentCopies: agents.length,
      stale: stale.map((agent) => agent.path || join(agent.skillsPath, "maestro")),
      ...(stale.length ? { message: "Some registered installations no longer exist." } : {}),
    };
  } catch (error) {
    checks.installations = { ok: false, message: String(error.message || error) };
  }

  try {
    const { path, data } = loadUserRunbooks();
    checks.runbooks = {
      ok: true,
      path,
      entries: Object.keys(data.skills).filter((name) => !name.startsWith("_")).length,
    };
  } catch (error) {
    checks.runbooks = { ok: false, message: String(error.message || error) };
  }

  const failed = Object.entries(checks)
    .filter(([, check]) => !check.ok)
    .map(([name]) => name);
  return {
    ok: failed.length === 0,
    version: packageVersion(),
    network: "not-used",
    home: paths.home,
    failed,
    checks,
  };
}

export function formatDoctor(payload) {
  const lines = [
    `Maestro ${payload.version} doctor (${payload.ok ? "healthy" : "needs attention"})`,
    `Home: ${payload.home}`,
    "Network: not used",
    "",
  ];
  for (const [name, check] of Object.entries(payload.checks)) {
    const detail = check.message || check.path || check.command || "ok";
    lines.push(`${check.ok ? "OK" : "FAIL"}  ${name}: ${detail}`);
  }
  return lines.join("\n");
}
