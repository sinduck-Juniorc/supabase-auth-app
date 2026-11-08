import { spawn, spawnSync } from "node:child_process";
import { existsSync } from "node:fs";

const env = { ...process.env, SUPABASE_URL: "http://127.0.0.1:55821", SUPABASE_PUBLISHABLE_KEY: "local-test-anon-key",
  APP_URL: "http://127.0.0.1:3000", NEXT_TELEMETRY_DISABLED: "1" };
if (existsSync("/usr/bin/chromium")) env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH = "/usr/bin/chromium";
const npm = process.env.npm_execpath;
if (!npm) throw new Error("npm run test:integration으로 실행하세요.");
function run(command, args) {
  const result = spawnSync(command, args, { env, stdio: "inherit" });
  if (result.status !== 0) throw new Error(`${command} 실행 실패: ${result.status}`);
}
let gateway;
try {
  run("docker", ["compose", "-f", "tests/stack.compose.yml", "up", "-d", "--wait"]);
  gateway = spawn(process.execPath, ["tests/auth-proxy.mjs"], { env, stdio: "inherit" });
  let ready = false;
  for (let i = 0; i < 60; i++) {
    try { if ((await fetch(env.SUPABASE_URL + "/auth/v1/health")).ok) { ready = true; break; } } catch {}
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  if (!ready) throw new Error("로컬 Auth 준비 시간 초과");
  run(process.execPath, [npm, "run", "build"]);
  run(process.execPath, [npm, "run", "test:e2e"]);
} catch (error) {
  spawnSync("docker", ["compose", "-f", "tests/stack.compose.yml", "logs", "--no-color", "--tail", "45"], { env, stdio: "inherit" });
  throw error;
} finally {
  gateway?.kill();
  spawnSync("docker", ["compose", "-f", "tests/stack.compose.yml", "down", "-v"], { env, stdio: "inherit" });
}
