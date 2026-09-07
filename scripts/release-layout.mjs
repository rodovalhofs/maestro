// Reviewed release inputs. New runtime/resources must be explicitly added here.
export const CLI_FILES = [
  "bin/cli.js", "agents.json", "lib/atomic-file.js", "lib/cli.js", "lib/commands.js",
  "lib/detect-agents.js", "lib/doctor.js", "lib/install.js", "lib/paths.js",
  "lib/python.js", "lib/remove.js", "lib/run-manifest.js", "lib/runbook.js", "lib/setup.js",
];
export const SKILL_FILES = {
  maestro: [
    "SKILL.md", "skill-runbooks.md", "skill-runbooks.json", "maestro-exclude.example.txt",
    "discover-allowlist.example.txt", "scripts/bm25.py", "scripts/build_manifest.py",
    "scripts/catalog.py", "scripts/concept_gaps.py", "scripts/discovery.py", "scripts/domains.py",
    "scripts/intents.py", "scripts/invoke.ps1", "scripts/invoke.sh", "scripts/maestro_paths.py",
    "scripts/route_tasks.py", "scripts/routing.py", "scripts/runbooks.py",
    "scripts/search_skills.py", "scripts/synonyms.py", "scripts/text_normalization.py",
  ],
  "maestro-prompt-designer": ["SKILL.md", "references/task-spec-template.md"],
};
export const PACKAGED_DIRS = { maestro: "skill", "maestro-prompt-designer": "designer" };
export const RELEASE_FILES = [
  "package.json", "README.md", "LICENSE", ...CLI_FILES,
  ...Object.entries(SKILL_FILES).flatMap(([skill, files]) => files.map((file) => `${PACKAGED_DIRS[skill]}/${file}`)),
].sort();
