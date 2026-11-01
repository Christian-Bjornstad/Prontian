// Parse maintained Mermaid diagrams without executing application code.
import fs from "node:fs";
import path from "node:path";
import { JSDOM } from "jsdom";

// Mermaid sanitizes labels while parsing. Supply a private synthetic DOM; no
// network resources or application pages are loaded.
const dom = new JSDOM("<!doctype html><html><body></body></html>");
globalThis.window = dom.window;
globalThis.document = dom.window.document;
const { default: mermaid } = await import("mermaid");

mermaid.initialize({ startOnLoad: false });
const files = [
  "README.md",
  ...fs
    .readdirSync("docs", { recursive: true })
    .filter((name) => name.endsWith(".md"))
    .map((name) => path.join("docs", name)),
];
let count = 0;
for (const file of files) {
  const source = fs.readFileSync(file, "utf8");
  for (const match of source.matchAll(/```mermaid\s*\n([\s\S]*?)```/g)) {
    try {
      await mermaid.parse(match[1]);
      count += 1;
    } catch (error) {
      throw new Error(`Invalid Mermaid in ${file}: ${error.message}`, {
        cause: error,
      });
    }
  }
}
if (count < 7)
  throw new Error("Expected architecture, flow, ER and state diagrams.");
console.log(`Mermaid: ${count} diagrams parsed.`);
