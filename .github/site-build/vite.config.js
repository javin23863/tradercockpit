import { defineConfig } from "vite";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

const here = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
  build: {
    outDir: resolve(here, "../../docs/assets/generated"),
    emptyOutDir: false,
    cssCodeSplit: false,
    sourcemap: false,
    minify: "oxc",
    lib: {
      entry: resolve(here, "src/site-webgl.js"),
      name: "TraderCockpitWebGL",
      formats: ["iife"],
      fileName: () => "site-webgl-v1.js",
    },
  },
});
