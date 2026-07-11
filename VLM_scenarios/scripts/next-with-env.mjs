import { spawn } from "node:child_process";
import { createRequire } from "node:module";

import nextEnv from "@next/env";

const require = createRequire(import.meta.url);
const command = process.argv[2] || "dev";
const projectDir = process.cwd();
const { loadEnvConfig } = nextEnv;

loadEnvConfig(projectDir);

const nextBin = require.resolve("next/dist/bin/next");
const args = [nextBin, command];

if ((command === "dev" || command === "start") && process.env.PORT) {
  args.push("--port", process.env.PORT);
}

const child = spawn(process.execPath, args, {
  env: process.env,
  stdio: "inherit",
});

child.on("exit", (code) => {
  process.exit(code ?? 0);
});
