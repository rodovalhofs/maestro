import { spawnSync } from "node:child_process";
import { runBuildManifest } from "./python.js";

export { runBuildManifest };

export async function registerOnSkillsSh(agents, { yes = false, interactive = false } = {}) {
  const withCli = agents.filter((a) => a.skillsCliAgent);
  if (!withCli.length) return { ok: true, skipped: true };

  const uniqueAgents = [...new Set(withCli.map((a) => a.skillsCliAgent))];
  const baseArgs = [
    "skills",
    "add",
    "rodovalhofs/maestro",
    "--skill",
    "maestro",
    "-g",
    ...uniqueAgents.flatMap((a) => ["-a", a]),
  ];

  const manual = `npx ${baseArgs.join(" ")}`;

  if (!yes && !interactive) {
    return {
      ok: true,
      skipped: true,
      manual_command: manual,
      note: "Review the package on GitHub before running.",
    };
  }

  const finalArgs = interactive ? baseArgs : [...baseArgs, "-y"];
  const result = spawnSync("npx", finalArgs, {
    encoding: "utf8",
    stdio: interactive ? "inherit" : "pipe",
    shell: process.platform === "win32",
  });

  if (result.status !== 0) {
    return {
      ok: false,
      error: "npx skills add failed (optional step).",
      manual_command: manual,
    };
  }
  return { ok: true };
}
