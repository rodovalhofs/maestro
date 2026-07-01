#!/usr/bin/env node
import { Command } from "commander";
import { runRemove } from "../lib/remove.js";
import { runSetup } from "../lib/setup.js";

const program = new Command();
program.name("maestro").description("Maestro skill orchestrator (@rodovalhofs/maestro)").version("0.1.0");
program.command("setup").description("Interactive setup").option("--project").option("--cursor").option("--claude").option("--codex").option("--universal").option("-y, --yes").option("--no-skills-registry").action(runSetup);
program.command("remove").description("Remove Maestro").option("-y, --yes").option("--all").option("--clean-home").action(runRemove);
program.parseAsync(process.argv);
