import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { join } from "node:path";
import {
  bundledBuildManifest,
  bundledScript,
  getMaestroPaths,
  skillSourceDir,
} from "./paths.js";

export function pythonCommand() {
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

/** Stable UTF-8 for Python child stdout/stderr on Windows (cp1252/cp850 consoles). */
export function pythonSpawnEnv() {
  return {
    ...process.env,
    PYTHONIOENCODING: "utf-8",
    PYTHONUTF8: "1",
  };
}

export function resolveScript(name, installedSkillPath = null) {
  const fromBundle = bundledScript(name);
  if (existsSync(fromBundle)) return fromBundle;
  if (installedSkillPath) {
    const alt = join(installedSkillPath, "scripts", name);
    if (existsSync(alt)) return alt;
  }
  return fromBundle;
}

export function runPythonScript(scriptName, args = [], { quiet = false } = {}) {
  const py = pythonCommand();
  if (!py) {
    return {
      ok: false,
      error: "Python 3.12+ not found. Install Python or use WSL/macOS python3.",
      code: 127,
    };
  }

  const script = resolveScript(scriptName);
  if (!existsSync(script)) {
    return { ok: false, error: `Script not found: ${script}`, code: 1 };
  }

  const result = spawnSync(py[0], [...py.slice(1), script, ...args], {
    encoding: "utf8",
    env: pythonSpawnEnv(),
    stdio: quiet ? "pipe" : "inherit",
    shell: false,
  });

  if (result.status !== 0) {
    return {
      ok: false,
      error: result.stderr?.trim() || `Exited with code ${result.status}`,
      code: result.status ?? 1,
      stdout: result.stdout || "",
    };
  }

  return {
    ok: true,
    stdout: result.stdout || "",
    code: 0,
  };
}

export function runBuildManifest({
  projectRoot = process.cwd(),
  quiet = false,
  installedSkillPath = null,
} = {}) {
  const { manifest } = getMaestroPaths();
  return runPythonScript(
    "build_manifest.py",
    ["--project-root", projectRoot, "--output", manifest],
    { quiet },
  );
}

export function skillRootHint() {
  try {
    return skillSourceDir();
  } catch {
    return null;
  }
}

export { bundledBuildManifest };
