import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { join } from "node:path";
import { bundledBuildManifest, getMaestroPaths } from "./paths.js";

function pythonCommand() {
  if (process.platform === "win32") {
    const py = spawnSync("py", ["-3", "--version"], { encoding: "utf8" });
    if (py.status === 0) return ["py", "-3"];
  }
  const python3 = spawnSync("python3", ["--version"], { encoding: "utf8" });
  if (python3.status === 0) return ["python3"];
  const python = spawnSync("python", ["--version"], { encoding: "utf8" });
  if (python.status === 0) return ["python"];
  return null;
}

export function runBuildManifest({
  projectRoot = process.cwd(),
  quiet = false,
  installedSkillPath = null,
} = {}) {
  let script = bundledBuildManifest();
  if (!existsSync(script) && installedSkillPath) {
    script = join(installedSkillPath, "scripts", "build_manifest.py");
  }
  if (!existsSync(script)) {
    return { ok: false, error: `build_manifest.py not found at ${script}` };
  }

  const py = pythonCommand();
  if (!py) {
    return {
      ok: false,
      error: "Python 3.12+ not found. Install Python and ensure `py -3` or `python3` works.",
    };
  }

  const { manifest } = getMaestroPaths();
  const args = [...py, script, "--project-root", projectRoot, "--output", manifest];
  const result = spawnSync(args[0], args.slice(1), {
    encoding: "utf8",
    stdio: quiet ? "pipe" : "inherit",
  });

  if (result.status !== 0) {
    return {
      ok: false,
      error: result.stderr || `build_manifest exited with code ${result.status}`,
    };
  }

  const line = (result.stdout || "").trim().split("\n").pop();
  return { ok: true, message: line || `Manifest written to ${manifest}` };
}

export async function registerOnSkillsSh(agents, { yes = false } = {}) {
  const withCli = agents.filter((a) => a.skillsCliAgent);
  if (!withCli.length) return { ok: true, skipped: true };

  const args = [
    "skills",
    "add",
    "rodovalhofs/maestro",
    "--skill",
    "maestro",
    "-g",
    "-y",
  ];

  for (const agent of withCli) {
    args.push("-a", agent.skillsCliAgent);
  }

  const uniqueAgents = [...new Set(withCli.map((a) => a.skillsCliAgent))];
  const finalArgs = [
    "skills",
    "add",
    "rodovalhofs/maestro",
    "--skill",
    "maestro",
    "-g",
    "-y",
    ...uniqueAgents.flatMap((a) => ["-a", a]),
  ];

  const result = spawnSync("npx", finalArgs, {
    encoding: "utf8",
    stdio: yes ? "pipe" : "inherit",
    shell: process.platform === "win32",
  });

  if (result.status !== 0) {
    return {
      ok: false,
      error: "npx skills add failed (optional step). Install Node.js or run manually.",
    };
  }
  return { ok: true };
}
