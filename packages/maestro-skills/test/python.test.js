import { test } from "node:test";
import assert from "node:assert/strict";
import { pythonSpawnEnv } from "../lib/python.js";

test("pythonSpawnEnv forces UTF-8 for child Python on Windows", () => {
  const env = pythonSpawnEnv();
  assert.equal(env.PYTHONIOENCODING, "utf-8");
  assert.equal(env.PYTHONUTF8, "1");
});
