import { existsSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { loadAgents } from "./paths.js";

export function detectAgents({ project = false, cwd = process.cwd(), home = homedir() } = {}) {
  const agents = loadAgents();
  const base = project ? cwd : home;

  return agents.map((agent) => {
    const detected = agent.detectDirs.some((dir) => existsSync(join(base, dir)));
    return {
      ...agent,
      detected,
      skillsPath: join(base, project ? agent.projectSkillsDir : agent.globalSkillsDir),
    };
  });
}

export function filterAgentsByFlags(agents, flags) {
  const ids = [];
  if (flags.cursor) ids.push("cursor");
  if (flags.claude) ids.push("claude");
  if (flags.codex) ids.push("codex");
  if (flags.universal) ids.push("universal");
  if (!ids.length) return agents;
  return agents.filter((a) => ids.includes(a.id));
}
