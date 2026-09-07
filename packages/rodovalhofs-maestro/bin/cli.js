#!/usr/bin/env node
import { runCli } from "../lib/cli.js";

await runCli({
  name: "maestro",
  description: "Maestro skill orchestrator (@rodovalhofs/maestro)",
});
