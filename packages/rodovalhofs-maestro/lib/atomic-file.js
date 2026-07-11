import { randomUUID } from "node:crypto";
import { mkdirSync, renameSync, rmSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";

export function writeFileAtomic(path, content, { mode = 0o600 } = {}) {
  mkdirSync(dirname(path), { recursive: true });
  const temporary = `${path}.${process.pid}.${randomUUID()}.tmp`;
  try {
    writeFileSync(temporary, content, {
      encoding: "utf8",
      flag: "wx",
      mode,
    });
    renameSync(temporary, path);
  } finally {
    rmSync(temporary, { force: true });
  }
}
