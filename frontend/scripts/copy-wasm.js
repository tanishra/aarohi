const { copyFileSync, mkdirSync, readdirSync, readFileSync, writeFileSync } = require("fs");
const { join } = require("path");

const sdkDir = join(__dirname, "..", "node_modules", "@spatius", "avatarkit", "dist");
const publicDir = join(__dirname, "..", "public", "_avatarkit");

mkdirSync(publicDir, { recursive: true });

const files = readdirSync(sdkDir);
for (const file of files) {
  if (file.startsWith("avatar_core_wasm") && file.endsWith(".wasm")) {
    copyFileSync(join(sdkDir, file), join(publicDir, file));
    console.log("[avatarkit] Copied WASM:", file);
  }
  if (file.startsWith("avatar_core_wasm") && file.endsWith(".js")) {
    const wasmFile = files.find((f) => f.startsWith("avatar_core_wasm") && f.endsWith(".wasm"));
    const jsPath = join(sdkDir, file);
    let content = readFileSync(jsPath, "utf-8");
    const patched = content
      .replace(
        /scriptDirectory\s*=\s*new\s+URL\(\s*"\."\s*,\s*_scriptName\s*\)\.href\s*;/,
        'scriptDirectory = "/_avatarkit/";',
      )
      .replace(
        /scriptDirectory\s*=\s*"";/,
        'scriptDirectory = "/_avatarkit/";',
      );
    if (patched !== content) {
      writeFileSync(jsPath, patched);
      console.log("[avatarkit] Patched scriptDirectory in:", file);
    }
  }
}

console.log("[avatarkit] Done.");
