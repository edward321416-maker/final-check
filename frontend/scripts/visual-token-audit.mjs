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

const TYPE_ROLES = [
  ["display-lg", 56, 64],
  ["display-md", 48, 56],
  ["heading-1", 40, 48],
  ["heading-2", 32, 40],
  ["heading-3", 24, 32],
  ["heading-4", 20, 28],
  ["body-lg", 16, 24],
  ["body", 14, 20],
  ["small", 12, 16],
  ["micro", 11, 16],
];
const TYPE_PAIRS = new Map(TYPE_ROLES.map(([, size, line]) => [size, line]));
const TYPE_SIZE_TOKENS = new Map(TYPE_ROLES.map(([role, size]) => [`--type-${role}-size`, { role, pixels: size }]));
const TYPE_LINE_TOKENS = new Map(TYPE_ROLES.map(([role, , line]) => [`--type-${role}-line`, { role, pixels: line }]));
const SPACE_TOKENS = new Set(Array.from({ length: 12 }, (_, index) => `--space-${index}`));
const RADIUS_TOKENS = new Set(Array.from({ length: 4 }, (_, index) => `--radius-${index}`));
const BORDER_TOKENS = new Set(["--border-1", "--border-2", "--border-3"]);
const COLOR_TOKENS = new Set([
  "--page", "--surface", "--surface-subtle",
  "--text-primary", "--text-secondary", "--text-muted", "--text-faint",
  "--border-subtle", "--border-strong",
  "--accent", "--accent-hover", "--accent-soft",
  "--status-blocker", "--status-blocker-soft",
  "--status-review", "--status-review-soft",
  "--status-pass", "--status-pass-soft",
  "--status-external", "--status-external-soft",
]);

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
  "border-block", "border-block-start", "border-block-end",
  "border-inline", "border-inline-start", "border-inline-end",
]);

const TEXT_PAINT_SHORTHANDS = new Set([
  "text-emphasis", "-webkit-text-emphasis", "text-stroke", "-webkit-text-stroke",
]);

const WIDTH_AND_COLOR_SHORTHANDS = new Set([
  ...BORDER_SHORTHANDS, "text-stroke", "-webkit-text-stroke",
]);

const ICON_SIZE_PROPERTIES = new Set(["width", "height", "min-width", "min-height"]);
const ICON_SELECTOR = /\.(?:scan-check|dot|alert-symbol|drawer-close|file-icon|upload-glyph)(?![\w-])/;
const RAW_COLOR_FUNCTION = /#[0-9a-f]{3,8}\b|\b(?:rgb|rgba|hsl|hsla|hwb|lab|lch|oklab|oklch|color|color-mix|light-dark|contrast-color|device-cmyk)\s*\(/i;
const NAMED_COLORS = new Set((
  "aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue blueviolet brown burlywood " +
  "cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue darkcyan darkgoldenrod darkgray " +
  "darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid darkred darksalmon darkseagreen " +
  "darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink deepskyblue dimgray dimgrey dodgerblue " +
  "firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite gold goldenrod gray green greenyellow grey honeydew " +
  "hotpink indianred indigo ivory khaki lavender lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan " +
  "lightgoldenrodyellow lightgray lightgreen lightgrey lightpink lightsalmon lightseagreen lightskyblue lightslategray " +
  "lightslategrey lightsteelblue lightyellow lime limegreen linen magenta maroon mediumaquamarine mediumblue mediumorchid " +
  "mediumpurple mediumseagreen mediumslateblue mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream " +
  "mistyrose moccasin navajowhite navy oldlace olive olivedrab orange orangered orchid palegoldenrod palegreen " +
  "paleturquoise palevioletred papayawhip peachpuff peru pink plum powderblue purple rebeccapurple red rosybrown royalblue " +
  "saddlebrown salmon sandybrown seagreen seashell sienna silver skyblue slateblue slategray slategrey snow springgreen " +
  "steelblue tan teal thistle tomato turquoise violet wheat white whitesmoke yellow yellowgreen accentcolor accentcolortext " +
  "activetext buttonborder buttonface buttontext canvas canvastext field fieldtext graytext highlight highlighttext linktext " +
  "mark marktext selecteditem selecteditemtext visitedtext"
).split(/\s+/));
const GENERATED_DIRECTORIES = new Set([".next", "node_modules", "dist", "build", "out", "coverage", "generated", "__generated__"]);

function pxNumbers(value) {
  return [...value.matchAll(/(-?\d+(?:\.\d+)?)px/g)].map(match => Number(match[1]));
}

function usesVariableOrLayoutExpression(value) {
  return /var\(|calc\(|min\(|max\(/i.test(value);
}

function add(findings, file, property, value, reason) {
  findings.push({ file, property, value: value.trim(), reason });
}

function withoutImportant(value) {
  return value.replace(/\s*!important\s*$/i, "").trim();
}

function variableNames(value) {
  return [...value.matchAll(/var\(\s*(--[\w-]+)/gi)].map(match => match[1]);
}

function hasOnlyAllowedVariables(value, allowed) {
  if (!usesVariableOrLayoutExpression(value) || !/var\(/i.test(value)) return true;
  const names = variableNames(value);
  return names.length > 0 && names.every(name => allowed.has(name));
}

function hasUnapprovedLength(value, approved, { allowPercent = false } = {}) {
  const dimensions = [...value.matchAll(/(-?(?:\d+(?:\.\d+)?|\.\d+))([a-z]+|%)/gi)];
  return dimensions.some(([, rawNumber, rawUnit]) => {
    const unit = rawUnit.toLowerCase();
    if (unit === "%") return !allowPercent;
    if (unit !== "px") return true;
    const number = Number(rawNumber);
    return !Number.isInteger(number) || !approved.has(number);
  });
}

function typographyValue(value, tokenMap, approved) {
  const variable = value.match(/^var\(\s*(--[\w-]+)\s*\)$/i);
  if (variable) return tokenMap.get(variable[1]) ?? null;
  const literal = value.match(/^(-?\d+(?:\.\d+)?)px$/i);
  if (!literal) return null;
  const pixels = Number(literal[1]);
  return Number.isInteger(pixels) && approved.has(pixels) ? { role: null, pixels } : null;
}

function containsNamedColor(value) {
  return (value.toLowerCase().match(/[a-z]+/g) ?? []).some(word => NAMED_COLORS.has(word));
}

function containsPaintFunction(value) {
  return /\b(?:(?:repeating-)?(?:linear|radial|conic)-gradient|drop-shadow)\s*\(/i.test(value);
}

function skipQuoted(value, start) {
  const quote = value[start];
  let index = start + 1;
  while (index < value.length) {
    if (value[index] === "\\") {
      index += 2;
    } else if (value[index] === quote) {
      return index + 1;
    } else {
      index += 1;
    }
  }
  return index;
}

function colorTokensOnly(value) {
  let result = "";
  let index = 0;

  while (index < value.length) {
    if (value[index] === "\"" || value[index] === "'") {
      index = skipQuoted(value, index);
      result += " ";
      continue;
    }

    const url = value.slice(index).match(/^url\s*\(/i);
    const boundary = index === 0 || !/[\w-]/.test(value[index - 1]);
    if (url && boundary) {
      index += url[0].length;
      let depth = 1;
      while (index < value.length && depth > 0) {
        if (value[index] === "\"" || value[index] === "'") {
          index = skipQuoted(value, index);
        } else if (value[index] === "\\") {
          index += 2;
        } else {
          if (value[index] === "(") depth += 1;
          if (value[index] === ")") depth -= 1;
          index += 1;
        }
      }
      result += " ";
      continue;
    }

    result += value[index];
    index += 1;
  }

  return result.replace(/var\(\s*--[\w-]+/gi, "var(");
}

function isColorProperty(property) {
  return property === "color" || property === "background" || property === "background-color" ||
    property === "background-image" || property.endsWith("-color") || BORDER_SHORTHANDS.has(property) ||
    TEXT_PAINT_SHORTHANDS.has(property) ||
    property === "outline" || property === "box-shadow" || property === "text-shadow" ||
    property === "fill" || property === "stroke" || property === "caret-color" ||
    property === "column-rule" || property === "text-decoration";
}

function allowedColorVariables(property) {
  if (property === "box-shadow") return new Set(["--shadow-overlay"]);
  if (WIDTH_AND_COLOR_SHORTHANDS.has(property) || property === "outline" || property === "column-rule") {
    return new Set([...COLOR_TOKENS, ...BORDER_TOKENS]);
  }
  return COLOR_TOKENS;
}

export function auditCssText(source, filename) {
  const findings = [];
  const css = source.replace(/\/\*[\s\S]*?\*\//g, "");
  const tokenFile = path.basename(filename) === COLOR_FILE;
  const blockPattern = /([^{}]+)\{([^{}]*)\}/g;

  for (const block of css.matchAll(blockPattern)) {
    const selector = block[1].trim();
    const body = block[2];
    const declarationPattern = /([\w-]+)\s*:\s*([^;]+?)(?:;|$)/g;
    let fontSize = null;
    let lineHeight = null;

    for (const declaration of body.matchAll(declarationPattern)) {
      const property = declaration[1].toLowerCase();
      const reportedValue = declaration[2].trim();
      const value = withoutImportant(reportedValue);

      if (property === "font") {
        add(findings, filename, property, reportedValue, "font shorthand is not allowed");
      } else if (property === "font-size") {
        if (/clamp\(|\d(?:\.\d+)?vw\b/i.test(value)) {
          add(findings, filename, property, reportedValue, "responsive typography is not allowed for font-size");
        } else {
          fontSize = typographyValue(value, TYPE_SIZE_TOKENS, TYPE);
          if (!fontSize) add(findings, filename, property, reportedValue, "unapproved font-size token");
        }
      } else if (property === "line-height") {
        lineHeight = typographyValue(value, TYPE_LINE_TOKENS, LINE);
        if (!lineHeight) add(findings, filename, property, reportedValue, "unapproved line-height token");
      } else if (SPACING_PROPERTIES.has(property)) {
        if (!hasOnlyAllowedVariables(value, SPACE_TOKENS) || hasUnapprovedLength(value, SPACE, { allowPercent: true })) {
          add(findings, filename, property, reportedValue, "unapproved spacing token");
        }
      } else if (property === "border-radius") {
        if (!hasOnlyAllowedVariables(value, RADIUS_TOKENS) || hasUnapprovedLength(value, RADIUS)) {
          add(findings, filename, property, reportedValue, "unapproved radius token");
        }
      } else if (BORDER_WIDTH_PROPERTIES.has(property)) {
        if (!hasOnlyAllowedVariables(value, BORDER_TOKENS) || hasUnapprovedLength(value, BORDER) || /\b(?:thin|medium|thick)\b/i.test(value)) {
          add(findings, filename, property, reportedValue, "unapproved border width token");
        }
      } else if (BORDER_SHORTHANDS.has(property)) {
        const borderTokens = new Set([...BORDER_TOKENS, ...COLOR_TOKENS]);
        if (!hasOnlyAllowedVariables(value, borderTokens) || hasUnapprovedLength(value, BORDER) || /\b(?:thin|medium|thick)\b/i.test(value)) {
          add(findings, filename, property, reportedValue, "unapproved border width token");
        }
      } else if (property === "font-weight") {
        const normalized = value.toLowerCase();
        const weight = normalized === "normal" ? 400 : normalized === "bold" ? 700 : Number(value);
        if (!Number.isInteger(weight) || !WEIGHTS.has(weight)) {
          add(findings, filename, property, reportedValue, "unapproved font weight token");
        }
      } else if (property === "letter-spacing") {
        const match = value.match(/^(-?\d+(?:\.\d+)?)px$/i);
        if (value.toLowerCase() !== "normal" && (!match || !Number.isInteger(Number(match[1])) || !LETTER.has(Number(match[1])))) {
          add(findings, filename, property, reportedValue, "unapproved letter spacing token");
        }
      }

      const colorProperty = isColorProperty(property);
      const colorValue = colorTokensOnly(value);
      const namedColorPosition = colorProperty || property.startsWith("--") || containsPaintFunction(colorValue);
      const rawColor = RAW_COLOR_FUNCTION.test(colorValue) ||
        (namedColorPosition && containsNamedColor(colorValue));
      if (!tokenFile && rawColor) {
        add(findings, filename, property, reportedValue, "raw color must use a visual token");
      }

      if (!tokenFile && colorProperty && !hasOnlyAllowedVariables(value, allowedColorVariables(property))) {
        add(findings, filename, property, reportedValue, "unapproved color token");
      }

      if (!tokenFile && property === "box-shadow" && value !== "var(--shadow-overlay)" && value.toLowerCase() !== "none") {
        add(findings, filename, property, reportedValue, "box-shadow must use var(--shadow-overlay) or none");
      }

      if (ICON_SELECTOR.test(selector) && ICON_SIZE_PROPERTIES.has(property) &&
          (!hasOnlyAllowedVariables(value, SPACE_TOKENS) || hasUnapprovedLength(value, SPACE))) {
        add(findings, filename, property, reportedValue, "unapproved spacing token for fixed icon size");
      }
    }

    if (fontSize && lineHeight) {
      const roleMismatch = fontSize.role && lineHeight.role && fontSize.role !== lineHeight.role;
      const valueMismatch = TYPE_PAIRS.get(fontSize.pixels) !== lineHeight.pixels;
      if (roleMismatch || valueMismatch) {
        const sizeDeclaration = [...body.matchAll(/font-size\s*:\s*([^;]+?)(?:;|$)/g)].at(-1)?.[1].trim() ?? String(fontSize.pixels);
        const lineDeclaration = [...body.matchAll(/line-height\s*:\s*([^;]+?)(?:;|$)/g)].at(-1)?.[1].trim() ?? String(lineHeight.pixels);
        add(findings, filename, "font-size/line-height", `${sizeDeclaration} / ${lineDeclaration}`, "unapproved typography pair");
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
      const normalizedName = entry.name.toLowerCase();
      if (entry.isDirectory() && GENERATED_DIRECTORIES.has(normalizedName)) continue;

      const absolute = path.join(directory, entry.name);
      if (entry.isDirectory()) {
        visit(absolute);
      } else if (entry.isFile() && normalizedName.endsWith(".css") && !normalizedName.endsWith(".generated.css") && !normalizedName.endsWith(".min.css")) {
        files.push(absolute);
      }
    }
  }

  visit(path.join(frontendRoot, "app"));
  visit(path.join(frontendRoot, "components"));
  return files.sort((left, right) => left < right ? -1 : left > right ? 1 : 0);
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

  if (findings.length === 0) {
    console.log("Visual token audit: 0 findings");
  }

  process.exitCode = findings.length > 0 ? 1 : 0;
}
