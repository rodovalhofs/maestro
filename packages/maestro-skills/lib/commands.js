import { spawnSync } from "node:child_process";
import { pythonCommand, pythonSpawnEnv, resolveScript, runPythonScript } from "./python.js";
import { getMaestroPaths } from "./paths.js";

export function runSearch(query, options = {}) {
  const { manifest } = getMaestroPaths();
  const args = [query, "--manifest", manifest, "--json"];
  if (options.domain) args.push("--domain", options.domain);
  if (options.projectRoot) args.push("--project-root", options.projectRoot);
  if (options.projectName) args.push("--project-name", options.projectName);
  if (options.maxResults) args.push("--max-results", String(options.maxResults));

  const result = runPythonScript("search_skills.py", args, { quiet: true });
  if (!result.ok) return withPythonMessage(result);

  try {
    return { ok: true, data: JSON.parse(result.stdout) };
  } catch {
    return { ok: false, error: "Invalid JSON from search_skills.py", stdout: result.stdout };
  }
}

export function runRoute(tasks, options = {}) {
  const { manifest } = getMaestroPaths();
  const input = (Array.isArray(tasks) ? tasks : [tasks]).join("\n");
  const args = ["--manifest", manifest, "--json"];
  if (options.domain) args.push("--domain", options.domain);

  const py = pythonCommand();
  if (!py) return { ok: false, error: "Python 3.10+ not found." };

  const script = resolveScript("route_tasks.py");
  const result = spawnSync(py[0], [...py.slice(1), script, ...args], {
    encoding: "utf8",
    env: pythonSpawnEnv(),
    input,
    stdio: ["pipe", "pipe", "pipe"],
  });

  if (result.status !== 0) {
    return withPythonMessage({
      ok: false,
      error: result.stderr?.trim() || "route_tasks failed",
      stdout: result.stdout || "",
    });
  }

  try {
    return { ok: true, data: JSON.parse(result.stdout) };
  } catch {
    return { ok: false, error: "Invalid JSON from route_tasks.py", stdout: result.stdout };
  }
}

function withPythonMessage(result) {
  try {
    const payload = JSON.parse(result.stdout || "");
    if (payload?.message) return { ...result, error: payload.message };
  } catch {
    // Preserve the process error when stdout was not structured JSON.
  }
  return result;
}
