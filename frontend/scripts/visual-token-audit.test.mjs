import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { auditCssText, auditTsxText, collectProductionCssFiles } from "./visual-token-audit.mjs";

function reasons(css) {
  return auditCssText(css, "fixture.css").map(item => item.reason);
}

test("canonical visual tokens retain their locked values", () => {
  const frontendRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
  const tokenFile = path.join(frontendRoot, "app", "visual-tokens.css");
  const tokenSource = fs.readFileSync(tokenFile, "utf8");
  const definitions = new Map(
    [...tokenSource.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)]
      .map(([, name, value]) => [name, value.trim()]),
  );
  const required = new Map([
    ["--page", "#FFFFFF"],
    ["--surface", "#FFFFFF"],
    ["--surface-subtle", "#FAFAF9"],
    ["--text-primary", "#0A0A0A"],
    ["--text-secondary", "#525252"],
    ["--text-muted", "#737373"],
    ["--text-faint", "#A3A3A3"],
    ["--border-subtle", "#E5E5E5"],
    ["--border-strong", "#D4D4D4"],
    ["--accent", "#3157FF"],
    ["--accent-hover", "#2447E6"],
    ["--accent-soft", "#F4F6FF"],
    ["--status-blocker", "#C62828"],
    ["--status-blocker-soft", "#FFF6F5"],
    ["--status-review", "#A15C00"],
    ["--status-review-soft", "#FFF9EB"],
    ["--status-pass", "#17824B"],
    ["--status-pass-soft", "#F0FBF5"],
    ["--status-external", "#737373"],
    ["--status-external-soft", "#F5F5F5"],
    ["--type-display-lg-size", "56px"],
    ["--type-display-lg-line", "64px"],
    ["--type-display-md-size", "48px"],
    ["--type-display-md-line", "56px"],
    ["--type-heading-1-size", "40px"],
    ["--type-heading-1-line", "48px"],
    ["--type-heading-2-size", "32px"],
    ["--type-heading-2-line", "40px"],
    ["--type-heading-3-size", "24px"],
    ["--type-heading-3-line", "32px"],
    ["--type-heading-4-size", "20px"],
    ["--type-heading-4-line", "28px"],
    ["--type-body-lg-size", "16px"],
    ["--type-body-lg-line", "24px"],
    ["--type-body-size", "14px"],
    ["--type-body-line", "20px"],
    ["--type-small-size", "12px"],
    ["--type-small-line", "16px"],
    ["--type-micro-size", "11px"],
    ["--type-micro-line", "16px"],
    ["--space-0", "0px"],
    ["--space-1", "4px"],
    ["--space-2", "8px"],
    ["--space-3", "12px"],
    ["--space-4", "16px"],
    ["--space-5", "24px"],
    ["--space-6", "32px"],
    ["--space-7", "48px"],
    ["--space-8", "64px"],
    ["--space-9", "80px"],
    ["--space-10", "96px"],
    ["--space-11", "120px"],
    ["--radius-0", "0px"],
    ["--radius-1", "4px"],
    ["--radius-2", "8px"],
    ["--radius-3", "12px"],
    ["--border-1", "1px"],
    ["--border-2", "2px"],
    ["--border-3", "3px"],
    ["--shadow-overlay", "0 16px 48px rgba(10, 10, 10, 0.12)"],
  ]);

  assert.deepEqual(definitions, required);
  assert.deepEqual(auditCssText(tokenSource, tokenFile), []);
});

test("canonicalizes valid escaped CSS property identifiers before classification", () => {
  const escapedHyphen = auditCssText(String.raw`
    .x {
      font\-size: 13px;
      line-height: 20px;
    }
  `, "fixture.css");
  const hexEscape = auditCssText(String.raw`
    .x { border\2d radius: 14px; }
  `, "fixture.css");
  const escapedCanonicalToken = auditCssText(String.raw`
    .x { --space\2d 4: 18px; }
  `, "fixture.css");

  assert(escapedHyphen.some(item => item.property === "font-size" && item.reason.includes("font-size")));
  assert(hexEscape.some(item => item.property === "border-radius" && item.reason.includes("radius")));
  assert(escapedCanonicalToken.some(item => item.property === "--space-4" && item.reason.includes("redeclared")));
});

test("rejects arithmetic composition for governed visual values", () => {
  const findings = auditCssText(`
    .x {
      border-width: calc(var(--border-1) * 99);
      padding: calc(var(--space-1) * 99);
    }
  `, "fixture.css");

  assert(findings.some(item => item.property === "border-width"));
  assert(findings.some(item => item.property === "padding"));
});

test("accepts direct governed tokens and exempt layout calculations", () => {
  const findings = auditCssText(`
    .x {
      border-width: var(--border-1);
      padding: var(--space-4);
      width: calc(100% - 24px);
      max-width: min(100%, 1240px);
      top: calc(var(--space-9) * -1);
      left: calc(var(--space-3) * -1);
    }
  `, "fixture.css");

  assert.deepEqual(findings, []);
});

test("recognizes only the exact canonical token authority path", () => {
  const frontendRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
  const canonicalFile = path.join(frontendRoot, "app", "visual-tokens.css");
  const nestedSpoof = path.join(frontendRoot, "components", "fake", "app", "visual-tokens.css");
  const basenameSpoof = path.join(frontendRoot, "components", "visual-tokens.css");
  const tokenSource = fs.readFileSync(canonicalFile, "utf8");
  const fakeSource = ":root { --page: #FFFFFF; }";

  assert.deepEqual(auditCssText(tokenSource, canonicalFile), []);
  for (const fakeFile of [nestedSpoof, basenameSpoof]) {
    const findings = auditCssText(fakeSource, fakeFile);
    assert(
      findings.some(item => item.property === "--page" && item.reason.includes("redeclared")),
      `${fakeFile} must not receive token authority`,
    );
    assert(findings.some(item => item.property === "--page" && item.reason.includes("raw color")));
  }
});

test("rejects incomplete, changed, or unexpected authoritative token definitions", () => {
  const frontendRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
  const tokenFile = path.join(frontendRoot, "app", "visual-tokens.css");
  const missing = auditCssText(":root { --page: #FFFFFF; }", tokenFile);
  const changed = auditCssText(":root { --space-4: 18px; }", tokenFile);
  const unexpected = auditCssText(":root { --rogue-space: 16px; }", tokenFile);
  const wrongScope = auditCssText(".component { --page: #FFFFFF; }", tokenFile);

  assert(missing.some(item => item.reason.includes("missing canonical token")));
  assert(changed.some(item => item.property === "--space-4" && item.reason.includes("canonical token value")));
  assert(unexpected.some(item => item.property === "--rogue-space" && item.reason.includes("unexpected visual token")));
  assert(wrongScope.some(item => item.property === "--page" && item.reason.includes(":root")));
});

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

test("rejects outline and every physical or logical border width bypass", () => {
  const properties = [
    "border-width", "border-top-width", "border-right-width", "border-bottom-width", "border-left-width",
    "border-block-width", "border-block-start-width", "border-block-end-width",
    "border-inline-width", "border-inline-start-width", "border-inline-end-width",
  ];
  const css = [
    ".outline { outline-width: 99px; outline-offset: 99px; outline: 99px solid var(--accent); }",
    ...properties.map((property, index) => `.border-${index} { ${property}: 99px; }`),
  ].join("\n");
  const findings = auditCssText(css, "fixture.css");

  for (const property of ["outline-width", "outline-offset", "outline", ...properties]) {
    assert(findings.some(item => item.property === property), `${property} must be audited`);
  }
});

test("rejects canonical token shadowing outside the authoritative token file", () => {
  const findings = auditCssText(".x { --space-4: 18px; padding: var(--space-4); }", "fixture.css");
  const disguised = auditCssText(".x { --space-4: 18px; }", "frontend/components/visual-tokens.css");
  assert(findings.some(item => item.property === "--space-4" && item.reason.includes("redeclared")));
  assert(disguised.some(item => item.property === "--space-4" && item.reason.includes("redeclared")));
});

test("rejects production TSX style attributes without matching code or string text", () => {
  const findings = auditTsxText(`
    const style = { padding: "18px" };
    const sample = '<div style={{ padding: "18px" }} />';
    export const View = () => <Panel child={<div style={style} />} />;
  `, "frontend/components/view.tsx");
  assert.deepEqual(findings.map(item => [item.property, item.value]), [["style", "style="]]);

  assert.deepEqual(
    auditTsxText("export const View = () => <div className=\"style=example\" />;", "frontend/components/view.tsx"),
    [],
  );
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

test("requires an explicit companion for every typography declaration", () => {
  const findings = auditCssText(`
    .token-size-only { font-size: var(--type-body-size); }
    .literal-size-only { font-size: 12px; }
    .token-line-only { line-height: var(--type-body-line); }
    .literal-line-only { line-height: 16px; }
  `, "fixture.css");
  const missingCompanions = findings.filter(item => item.reason.includes("missing companion"));

  assert.deepEqual(
    missingCompanions.map(item => [item.property, item.value]),
    [
      ["font-size/line-height", "var(--type-body-size) / missing"],
      ["font-size/line-height", "12px / missing"],
      ["font-size/line-height", "missing / var(--type-body-line)"],
      ["font-size/line-height", "missing / 16px"],
    ],
  );
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

test("collector and CLI include production CSS and TSX while excluding generated artifacts", t => {
  const workspace = fs.mkdtempSync(path.join(os.tmpdir(), "visual-token-audit-"));
  const frontendRoot = path.join(workspace, "frontend");
  const appRoot = path.join(frontendRoot, "app");
  const componentsRoot = path.join(frontendRoot, "components");
  t.after(() => fs.rmSync(workspace, { recursive: true, force: true }));

  fs.mkdirSync(path.join(appRoot, ".next"), { recursive: true });
  fs.mkdirSync(path.join(componentsRoot, "generated"), { recursive: true });
  fs.mkdirSync(path.join(workspace, "other"), { recursive: true });
  fs.writeFileSync(path.join(appRoot, "keep.css"), ".bad { color: red }\n");
  fs.writeFileSync(path.join(componentsRoot, "keep.module.css"), ".ok { color: var(--text-primary); }\n");
  fs.writeFileSync(path.join(componentsRoot, "inline.tsx"), "export const Bad = () => <div style={{ padding: '18px' }} />;\n");
  fs.writeFileSync(path.join(appRoot, ".next", "skip.css"), ".bad { color: white; }\n");
  fs.writeFileSync(path.join(componentsRoot, "generated", "skip.css"), ".bad { color: white; }\n");
  fs.writeFileSync(path.join(componentsRoot, "skip.generated.css"), ".bad { color: white; }\n");
  fs.writeFileSync(path.join(componentsRoot, "skip.min.css"), ".bad { color: white; }\n");
  fs.writeFileSync(path.join(workspace, "other", "skip.css"), ".bad { color: white; }\n");

  const relativeFiles = collectProductionCssFiles(frontendRoot)
    .map(file => path.relative(frontendRoot, file).replaceAll(path.sep, "/"));
  assert.deepEqual(relativeFiles, ["app/keep.css", "components/inline.tsx", "components/keep.module.css"]);

  const sourceScript = fileURLToPath(new URL("./visual-token-audit.mjs", import.meta.url));
  const cli = spawnSync(process.execPath, [sourceScript, "--check", "--frontend-root", frontendRoot], { encoding: "utf8" });
  assert.equal(cli.status, 1);
  assert.match(cli.stdout, /frontend\/app\/keep\.css :: color=red :: raw color/);
  assert.match(cli.stdout, /frontend\/components\/inline\.tsx :: style=/);
  assert.doesNotMatch(cli.stdout, /skip/);

  fs.writeFileSync(path.join(appRoot, "keep.css"), ".ok { color: var(--text-primary); }\n");
  fs.writeFileSync(path.join(componentsRoot, "inline.tsx"), "export const Good = () => <div className=\"ok\" />;\n");
  const cleanCli = spawnSync(process.execPath, [sourceScript, "--check", "--frontend-root", frontendRoot], { encoding: "utf8" });
  assert.equal(cleanCli.status, 0);
  assert.equal(cleanCli.stdout, "Visual token audit: 0 findings\n");
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
