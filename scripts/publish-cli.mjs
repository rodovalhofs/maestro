#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");
const target = process.argv[2] || "maestro-skills";
const allowed = new Set(["maestro-skills", "rodovalhofs-maestro"]);
if (!allowed.has(target)) {
  console.error(`Unknown publish target: ${target}`);
  process.exit(2);
}
const PKG = resolve(ROOT, "packages", target);

const sync = spawnSync("node", [resolve(__dirname, "sync-skill-to-cli.mjs"), "--target", target], {
  cwd: ROOT,
  stdio: "inherit",
});
if (sync.status !== 0) process.exit(sync.status ?? 1);

const publish = process.platform === "win32"
  ? spawnSync(
      process.env.ComSpec || "cmd.exe",
      ["/d", "/s", "/c", "npm publish --access public"],
      { cwd: PKG, stdio: "inherit", shell: false },
    )
  : spawnSync("npm", ["publish", "--access", "public"], {
      cwd: PKG,
      stdio: "inherit",
      shell: false,
    });
process.exit(publish.status ?? 1);
