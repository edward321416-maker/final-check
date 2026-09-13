import test from "node:test";
import assert from "node:assert/strict";
import { auditCssText } from "./visual-token-audit.mjs";

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
