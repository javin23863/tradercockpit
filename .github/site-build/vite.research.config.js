import { defineConfig } from "vite";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import { copyFileSync, writeFileSync } from "node:fs";

const here = fileURLToPath(new URL(".", import.meta.url));
const outDir = resolve(here, "../../docs/assets/generated");
const vtkRoot = resolve(here, "node_modules/@kitware/vtk.js");

export default defineConfig({
  plugins: [{
    name: "research-vtk-provenance",
    closeBundle() {
      copyFileSync(resolve(vtkRoot, "LICENSE"), resolve(outDir, "research-vtk-v1.LICENSE.txt"));
      writeFileSync(resolve(outDir, "research-vtk-v1.PROVENANCE.json"), `${JSON.stringify({
        schema: "tradercockpit.research-vtk.v1", component: "@kitware/vtk.js", version: "36.14.2",
        license: "BSD-3-Clause", source: "https://github.com/Kitware/vtk-js", bundle: "research-vtk-v1.js",
        purpose: "Research Lab analytical 3D surfaces, point clouds and line families"
      }, null, 2)}\n`);
    }
  }],
  build: {
    outDir, emptyOutDir: false, cssCodeSplit: false, sourcemap: false, minify: "oxc", target: "esnext",
    lib: { entry: resolve(here, "src/research-vtk.js"), name: "TraderCockpitResearchVTK", formats: ["iife"], fileName: () => "research-vtk-v1.js" }
  }
});
