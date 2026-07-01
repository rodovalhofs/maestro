#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");
const PKG = resolve(ROOT, "packages", "maestro-skills");

const sync = spawnSync("node", [resolve(__dirname, "sync-skill-to-cli.mjs")], {
  cwd: ROOT,
  stdio: "inherit",
});
if (sync.status !== 0) process.exit(sync.status ?? 1);

const publish = spawnSync("npm", ["publish", "--access", "public"], {
  cwd: PKG,
  stdio: "inherit",
  shell: process.platform === "win32",
});
process.exit(publish.status ?? 1);
