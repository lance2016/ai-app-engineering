import { build } from "esbuild";
import { copyFile, mkdir } from "node:fs/promises";

await mkdir("dist", { recursive: true });
await build({
  entryPoints: ["src/main.js"],
  bundle: true,
  outfile: "dist/app.js",
  format: "iife",
  platform: "browser",
  target: "es2020",
});
await copyFile("index.html", "dist/index.html");
await copyFile("styles.css", "dist/styles.css");
