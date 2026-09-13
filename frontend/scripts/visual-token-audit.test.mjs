import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { auditCssText, collectProductionCssFiles } from "./visual-token-audit.mjs";

function reasons(css) {
  return auditCssText(css, "fixture.css").map(item => item.reason);
}

test("rejects unapproved visual values", () => {
  const result = reasons(`
    .x {
      font-size: 13px;
      line-height: 1.65;
      padding: 18px;
      gap: 10px;
      border-radius: 14px;
      border-width: 4px;
      font-weight: 650;
      letter-spacing: .4px;
      color: #2563eb;
    }
  `);
  assert(result.some(reason => reason.includes("font-size")));
  assert(result.some(reason => reason.includes("line-height")));
  assert(result.some(reason => reason.includes("spacing")));
  assert(result.some(reason => reason.includes("radius")));
  assert(result.some(reason => reason.includes("border width")));
  assert(result.some(reason => reason.includes("font weight")));
  assert(result.some(reason => reason.includes("letter spacing")));
  assert(result.some(reason => reason.includes("raw color")));
});

test("rejects interpolated typography", () => {
  const result = reasons(`.hero { font-size: clamp(40px, 4vw, 56px); line-height: 1.2; }`);
  assert(result.some(reason => reason.includes("responsive typography")));
});

test("accepts token-based declarations and layout calculations", () => {
  const findings = auditCssText(`
    .ok {
      font-size: var(--type-body-size);
      line-height: var(--type-body-line);
      padding: var(--space-4) var(--space-6);
      gap: var(--space-3);
      border-radius: var(--radius-1);
      border-width: var(--border-1);
      color: var(--text-primary);
      width: min(100%, 1240px);
      grid-template-columns: .82fr 1fr;
      opacity: .65;
    }
  `, "fixture.css");
  assert.deepEqual(findings, []);
});

test("rejects named colors and named gradient stops", () => {
  const findings = auditCssText(`
    .white { background: white; }
    .red { color: red; }
    .gradient { background: linear-gradient(black, var(--surface)); }
    .allowed { color: transparent; border-color: currentColor; background: none; }
  `, "fixture.css");
  const rawColors = findings.filter(item => item.reason.includes("raw color"));
  assert.equal(rawColors.length, 3);
  assert.deepEqual(rawColors.map(item => item.value), [
    "white",
    "red",
    "linear-gradient(black, var(--surface))",
  ]);
});

test("enforces canonical literal and token typography pairs", () => {
  const findings = auditCssText(`
    .literal-mismatch { font-size: 56px; line-height: 16px; }
    .token-mismatch {
      font-size: var(--type-display-lg-size);
      line-height: var(--type-micro-line);
    }
    .literal-ok { font-size: 56px; line-height: 64px; }
    .token-ok {
      font-size: var(--type-display-lg-size);
      line-height: var(--type-display-lg-line);
    }
  `, "fixture.css");
  const mismatches = findings.filter(item => item.reason.includes("typography pair"));
  assert.equal(mismatches.length, 2);
  assert(mismatches.some(item => item.value === "56px / 16px"));
  assert(mismatches.some(item => item.value.includes("--type-display-lg-size") && item.value.includes("--type-micro-line")));
});

test("rejects arbitrary variables and non-pixel fixed lengths", () => {
  const result = reasons(`
    .rogue {
      font-size: var(--rogue-size);
      line-height: var(--rogue-line);
      padding: var(--rogue-gap);
      margin: 1rem;
      border-radius: var(--rogue-radius);
      border-width: var(--rogue-border);
      border: 1rem solid var(--border-subtle);
      color: var(--rogue-color);
      letter-spacing: var(--rogue-letter);
    }
  `);
  assert(result.some(reason => reason.includes("font-size")));
  assert(result.some(reason => reason.includes("line-height")));
  assert(result.filter(reason => reason.includes("spacing")).length >= 2);
  assert(result.some(reason => reason.includes("radius")));
  assert(result.some(reason => reason.includes("border")));
  assert(result.some(reason => reason.includes("color token")));
  assert(result.some(reason => reason.includes("letter spacing")));
});

test("audits semicolonless terminal declarations", () => {
  const findings = auditCssText(`
    .color { color: #2563eb }
    .space { padding: 18px }
  `, "fixture.css");
  assert(findings.some(item => item.reason.includes("raw color")));
  assert(findings.some(item => item.reason.includes("spacing")));
});

test("accepts canonical tokens with important", () => {
  const findings = auditCssText(`
    .ok {
      font-size: var(--type-body-size) !important;
      line-height: var(--type-body-line) !important;
      padding: var(--space-4) !important;
      color: var(--text-primary) !important;
      box-shadow: var(--shadow-overlay) !important;
    }
  `, "fixture.css");
  assert.deepEqual(findings, []);
});

test("collector and CLI include production CSS and exclude generated artifacts", t => {
  const workspace = fs.mkdtempSync(path.join(os.tmpdir(), "visual-token-audit-"));
  const frontendRoot = path.join(workspace, "frontend");
  const appRoot = path.join(frontendRoot, "app");
  const componentsRoot = path.join(frontendRoot, "components");
  const scriptsRoot = path.join(frontendRoot, "scripts");
  t.after(() => fs.rmSync(workspace, { recursive: true, force: true }));

  fs.mkdirSync(path.join(appRoot, ".next"), { recursive: true });
  fs.mkdirSync(path.join(componentsRoot, "generated"), { recursive: true });
  fs.mkdirSync(path.join(workspace, "other"), { recursive: true });
  fs.mkdirSync(scriptsRoot, { recursive: true });
  fs.writeFileSync(path.join(appRoot, "keep.css"), ".bad { color: red }\n");
  fs.writeFileSync(path.join(componentsRoot, "keep.module.css"), ".ok { color: var(--text-primary); }\n");
  fs.writeFileSync(path.join(appRoot, ".next", "skip.css"), ".bad { color: white; }\n");
  fs.writeFileSync(path.join(componentsRoot, "generated", "skip.css"), ".bad { color: white; }\n");
  fs.writeFileSync(path.join(componentsRoot, "skip.generated.css"), ".bad { color: white; }\n");
  fs.writeFileSync(path.join(componentsRoot, "skip.min.css"), ".bad { color: white; }\n");
  fs.writeFileSync(path.join(workspace, "other", "skip.css"), ".bad { color: white; }\n");

  const relativeFiles = collectProductionCssFiles(frontendRoot)
    .map(file => path.relative(frontendRoot, file).replaceAll(path.sep, "/"));
  assert.deepEqual(relativeFiles, ["app/keep.css", "components/keep.module.css"]);

  const sourceScript = fileURLToPath(new URL("./visual-token-audit.mjs", import.meta.url));
  const cliScript = path.join(scriptsRoot, "visual-token-audit.mjs");
  fs.copyFileSync(sourceScript, cliScript);
  const cli = spawnSync(process.execPath, [cliScript, "--check"], { encoding: "utf8" });
  assert.equal(cli.status, 1);
  assert.match(cli.stdout, /frontend\/app\/keep\.css :: color=red :: raw color/);
  assert.doesNotMatch(cli.stdout, /skip/);

  fs.writeFileSync(path.join(appRoot, "keep.css"), ".ok { color: var(--text-primary); }\n");
  const cleanCli = spawnSync(process.execPath, [cliScript, "--check"], { encoding: "utf8" });
  assert.equal(cleanCli.status, 0);
  assert.equal(cleanCli.stdout, "");
});

test("rejects named gradient stops on color-bearing properties outside the property list", () => {
  const findings = auditCssText(`
    .border { border-image: linear-gradient(red, blue) 1; }
  `, "fixture.css");
  assert(findings.some(item => item.property === "border-image" && item.reason.includes("raw color")));
});

test("handles uppercase and mixed-case var functions without bypasses", () => {
  const rogue = auditCssText(`
    .rogue {
      padding: VAR(--rogue-gap);
      color: vAr(--rogue-color);
    }
  `, "fixture.css");
  assert(rogue.some(item => item.property === "padding" && item.reason.includes("spacing")));
  assert(rogue.some(item => item.property === "color" && item.reason.includes("color token")));

  const canonical = auditCssText(`
    .ok {
      font-size: VaR(--type-body-size);
      line-height: VAR(--type-body-line);
      padding: vAr(--space-4);
      color: VAR(--text-primary);
    }
  `, "fixture.css");
  assert.deepEqual(canonical, []);
});

test("ignores named colors inside strings and url payloads", () => {
  const findings = auditCssText(`
    :root { --asset-label: "red"; }
    .asset {
      content: 'blue';
      background-image: url("/icons/red.svg");
      mask-image: URL('/icons/blue.svg');
      border-image: linear-gradient(var(--accent), transparent) 1, url(/textures/black.png) 1;
    }
  `, "fixture.css");
  assert.deepEqual(findings, []);
});

test("distinguishes non-color identifiers from named colors in color positions", () => {
  const identifiers = auditCssText(`
    .motion {
      animation-name: red;
      font-family: blue;
      counter-reset: green 1;
    }
  `, "fixture.css");
  assert.deepEqual(identifiers, []);

  const colors = auditCssText(`
    .paint {
      color: red;
      border-image: linear-gradient(blue, var(--accent)) 1;
      background: var(--surface, green);
    }
  `, "fixture.css");
  assert.equal(colors.filter(item => item.reason.includes("raw color")).length, 3);
});

test("rejects named colors in paint-bearing shorthands without treating identifiers as colors", () => {
  const findings = auditCssText(`
    .paint {
      border-inline: 1px solid red;
      border-block-start: 2px dashed blue;
      text-emphasis: filled green;
      -webkit-text-stroke: 1px purple;
    }
    .identifiers {
      animation-name: red;
      font-family: blue;
      counter-reset: green 1;
    }
    .tokenized {
      border-block: var(--border-1) solid var(--border-subtle);
      text-emphasis: filled var(--accent);
      -webkit-text-stroke: var(--border-1) var(--text-primary);
    }
  `, "fixture.css");
  const rawColors = findings.filter(item => item.reason.includes("raw color"));
  assert.deepEqual(rawColors.map(item => item.property), [
    "border-inline",
    "border-block-start",
    "text-emphasis",
    "-webkit-text-stroke",
  ]);
  assert.equal(findings.length, 4);
  assert.equal(findings.some(item => ["animation-name", "font-family", "counter-reset"].includes(item.property)), false);
});
