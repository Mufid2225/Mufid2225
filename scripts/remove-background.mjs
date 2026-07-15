import { removeBackground } from "@imgly/background-removal-node";
import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const input = resolve(root, "foto2-noremove.jpeg");
const output = resolve(root, "assets/portrait-cutout.png");

const source = await readFile(input);
const image = new Blob([source], { type: "image/jpeg" });
const result = await removeBackground(image, {
  model: "medium",
  output: { format: "image/png", quality: 1, type: "foreground" },
  progress: (key, current, total) => {
    const percent = total ? Math.round((current / total) * 100) : 0;
    process.stdout.write(`\r${key}: ${percent}%`);
  },
});

await writeFile(output, Buffer.from(await result.arrayBuffer()));
process.stdout.write(`\nBackground removed: ${output}\n`);
