import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const TYPE = new Set([11, 12, 14, 16, 20, 24, 32, 40, 48, 56]);
const LINE = new Set([16, 20, 24, 28, 32, 40, 48, 56, 64]);
const SPACE = new Set([0, 4, 8, 12, 16, 24, 32, 48, 64, 80, 96, 120]);
const RADIUS = new Set([0, 4, 8, 12]);
const BORDER = new Set([0, 1, 2, 3]);
const WEIGHTS = new Set([400, 500, 600, 700]);
const LETTER = new Set([-1, 0, 1]);
const COLOR_FILE = "visual-tokens.css";

const SPACING_PROPERTIES = new Set([
  "margin", "margin-top", "margin-right", "margin-bottom", "margin-left",
  "padding", "padding-top", "padding-right", "padding-bottom", "padding-left",
  "gap", "row-gap", "column-gap", "inset", "top", "right", "bottom", "left",
  "scroll-margin", "scroll-margin-top", "scroll-margin-right", "scroll-margin-bottom", "scroll-margin-left",
]);

const BORDER_WIDTH_PROPERTIES = new Set([
  "border-width", "border-top-width", "border-right-width", "border-bottom-width", "border-left-width",
]);

const BORDER_SHORTHANDS = new Set([
  "border", "border-top", "border-right", "border-bottom", "border-left",
]);

const ICON_SIZE_PROPERTIES = new Set(["width", "height", "min-width", "min-height"]);
const ICON_SELECTOR = /\.(?:scan-check|dot|alert-symbol|drawer-close|file-icon|upload-glyph)(?![\w-])/;
const RAW_COLOR = /#[0-9a-f]{3,8}\b|\b(?:rgb|rgba|hsl|hsla)\s*\(/i;
const GENERATED_DIRECTORIES = new Set([".next", "node_modules", "dist", "build", "out", "coverage", "generated", "__generated__"]);

function pxNumbers(value) {
  return [...value.matchAll(/(-?\d+(?:\.\d+)?)px/g)].map(match => Number(match[1]));
}

function usesVariableOrLayoutExpression(value) {
  return /var\(|calc\(|min\(|max\(/.test(value);
}

function add(findings, file, property, value, reason) {
  findings.push({ file, property, value: value.trim(), reason });
}

function isVariable(value) {
  return /^var\([\s\S]+\)$/.test(value.trim());
}

function hasUnapprovedPx(value, approved) {
  return pxNumbers(value).some(number => !Number.isInteger(number) || !approved.has(number));
}

export function auditCssText(source, filename) {
  const findings = [];
  const css = source.replace(/\/\*[\s\S]*?\*\//g, "");
  const tokenFile = path.basename(filename) === COLOR_FILE;
  const blockPattern = /([^{}]+)\{([^{}]*)\}/g;

  for (const block of css.matchAll(blockPattern)) {
    const selector = block[1].trim();
    const body = block[2];
    const declarationPattern = /([\w-]+)\s*:\s*([^;]+);/g;

    for (const declaration of body.matchAll(declarationPattern)) {
      const property = declaration[1].toLowerCase();
      const value = declaration[2].trim();
      const variable = isVariable(value);

      if (property === "font") {
        add(findings, filename, property, value, "font shorthand is not allowed");
      } else if (property === "font-size" && !variable) {
        if (/clamp\(|\d(?:\.\d+)?vw\b/i.test(value)) {
          add(findings, filename, property, value, "responsive typography is not allowed for font-size");
        } else {
          const numbers = pxNumbers(value);
          if (numbers.length !== 1 || !/^[-+]?\d+(?:\.\d+)?px$/i.test(value) || hasUnapprovedPx(value, TYPE)) {
            add(findings, filename, property, value, "unapproved font-size token");
          }
        }
      } else if (property === "line-height" && !variable) {
        const numbers = pxNumbers(value);
        if (numbers.length !== 1 || !/^[-+]?\d+(?:\.\d+)?px$/i.test(value) || hasUnapprovedPx(value, LINE)) {
          add(findings, filename, property, value, "unapproved line-height token");
        }
      } else if (SPACING_PROPERTIES.has(property)) {
        const numbers = pxNumbers(value);
        if (numbers.length > 0 && hasUnapprovedPx(value, SPACE)) {
          add(findings, filename, property, value, "unapproved spacing token");
        } else if (numbers.length === 0 && usesVariableOrLayoutExpression(value)) {
          // Token variables and fluid layout expressions without fixed px values are allowed.
        }
      } else if (property === "border-radius" && hasUnapprovedPx(value, RADIUS)) {
        add(findings, filename, property, value, "unapproved radius token");
      } else if (BORDER_WIDTH_PROPERTIES.has(property) && !variable) {
        const numbers = pxNumbers(value);
        const isZero = value === "0";
        if ((!isZero && numbers.length === 0) || hasUnapprovedPx(value, BORDER)) {
          add(findings, filename, property, value, "unapproved border width token");
        }
      } else if (BORDER_SHORTHANDS.has(property) && !variable) {
        if (hasUnapprovedPx(value, BORDER)) {
          add(findings, filename, property, value, "unapproved border width token");
        }
      } else if (property === "font-weight" && !variable) {
        const normalized = value.toLowerCase();
        const weight = normalized === "normal" ? 400 : normalized === "bold" ? 700 : Number(value);
        if (!Number.isInteger(weight) || !WEIGHTS.has(weight)) {
          add(findings, filename, property, value, "unapproved font weight token");
        }
      } else if (property === "letter-spacing" && !variable) {
        const match = value.match(/^(-?\d+(?:\.\d+)?)px$/i);
        if (value.toLowerCase() !== "normal" && (!match || !Number.isInteger(Number(match[1])) || !LETTER.has(Number(match[1])))) {
          add(findings, filename, property, value, "unapproved letter spacing token");
        }
      }

      if (!tokenFile && RAW_COLOR.test(value)) {
        add(findings, filename, property, value, "raw color must use a visual token");
      }

      if (!tokenFile && property === "box-shadow" && value !== "var(--shadow-overlay)" && value.toLowerCase() !== "none") {
        add(findings, filename, property, value, "box-shadow must use var(--shadow-overlay) or none");
      }

      if (ICON_SELECTOR.test(selector) && ICON_SIZE_PROPERTIES.has(property) && hasUnapprovedPx(value, SPACE)) {
        add(findings, filename, property, value, "unapproved spacing token for fixed icon size");
      }
    }
  }

  return findings;
}

export function collectProductionCssFiles(frontendRoot) {
  const files = [];

  function visit(directory) {
    if (!fs.existsSync(directory)) return;

    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      if (entry.isDirectory() && GENERATED_DIRECTORIES.has(entry.name)) continue;

      const absolute = path.join(directory, entry.name);
      if (entry.isDirectory()) {
        visit(absolute);
      } else if (entry.isFile() && entry.name.endsWith(".css") && !entry.name.endsWith(".generated.css") && !entry.name.endsWith(".min.css")) {
        files.push(absolute);
      }
    }
  }

  visit(path.join(frontendRoot, "app"));
  visit(path.join(frontendRoot, "components"));
  return files.sort((left, right) => left.localeCompare(right));
}

const invokedAsScript = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);

if (invokedAsScript && process.argv.includes("--check")) {
  const frontendRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
  const repositoryRoot = path.dirname(frontendRoot);
  const findings = collectProductionCssFiles(frontendRoot).flatMap(file => {
    const displayFile = path.relative(repositoryRoot, file).replaceAll(path.sep, "/");
    return auditCssText(fs.readFileSync(file, "utf8"), displayFile);
  });

  for (const finding of findings) {
    console.log(`${finding.file} :: ${finding.property}=${finding.value} :: ${finding.reason}`);
  }

  process.exitCode = findings.length > 0 ? 1 : 0;
}
