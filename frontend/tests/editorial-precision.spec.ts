import { test, expect } from "@playwright/test";

test("landing uses the approved editorial type, white canvas, and no card shadow", async ({ page }, info) => {
  await page.goto("/");
  const body = page.locator("body");
  await expect(body).toHaveCSS("background-color", "rgb(255, 255, 255)");

  const hero = page.getByRole("heading", { level: 1, name: "제출 버튼을 누르기 전, 마지막 확인." });
  await expect(hero).toHaveCSS("font-size", info.project.name === "mobile" ? "32px" : "56px");
  await expect(hero).toHaveCSS("line-height", info.project.name === "mobile" ? "40px" : "64px");
  await expect(hero).toHaveCSS("font-weight", "700");

  const frame = page.getByRole("region", { name: "Preflight 결과 예시" });
  await expect(frame).toHaveCSS("box-shadow", "none");
  await expect(frame).toHaveCSS("border-radius", "8px");
});

test("primary controls use scarce accent and compact editorial geometry", async ({ page }) => {
  await page.goto("/");
  const cta = page.getByRole("link", { name: "제출 전 검사 시작하기" }).first();
  await expect(cta).toHaveCSS("background-color", "rgb(49, 87, 255)");
  await expect(cta).toHaveCSS("border-radius", "4px");
  await expect(cta).toHaveCSS("font-size", "14px");
  await expect(cta).toHaveCSS("line-height", "20px");
  await expect(cta).toHaveCSS("font-weight", "600");
});

test("header and five-step shell use the approved compact type and spacing", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/announcement");

  const header = page.locator(".site-header");
  await expect(header).toHaveCSS("padding-top", "24px");
  await expect(header).toHaveCSS("padding-left", "32px");
  await expect(header).toHaveCSS("column-gap", "32px");

  const brand = page.getByRole("link", { name: "FINAL CHECK 홈" });
  await expect(brand).toHaveCSS("column-gap", "8px");
  await expect(brand).toHaveCSS("font-size", "20px");
  await expect(brand).toHaveCSS("line-height", "28px");
  await expect(brand).toHaveCSS("font-weight", "700");
  await expect(brand).toHaveCSS("letter-spacing", "-1px");

  const firstStep = page.getByRole("navigation", { name: "검사 단계" }).locator(".step").first();
  await expect(firstStep).toHaveCSS("padding", "16px");
  await expect(firstStep).toHaveCSS("column-gap", "12px");
  await expect(firstStep).toHaveCSS("font-size", "12px");
  await expect(firstStep).toHaveCSS("line-height", "16px");
  await expect(firstStep).toHaveCSS("font-weight", "500");
});

test("proof and story metadata use approved editorial tokens", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");

  const proofHeading = page.locator(".mini-window-heading");
  await expect(proofHeading).toHaveCSS("padding-bottom", "16px");
  await expect(proofHeading).toHaveCSS("font-size", "11px");
  await expect(proofHeading).toHaveCSS("line-height", "16px");
  await expect(proofHeading).toHaveCSS("letter-spacing", "1px");

  const proofMetadata = page.locator(".mini-summary span").first();
  await expect(proofMetadata).toHaveCSS("padding", "4px 8px");
  await expect(proofMetadata).toHaveCSS("font-size", "11px");
  await expect(proofMetadata).toHaveCSS("line-height", "16px");

  const story = page.locator(".story-step").first();
  await expect(story).toHaveCSS("padding", "48px 0px");
  await expect(story.locator("h3")).toHaveCSS("font-size", "24px");
  await expect(story.locator("h3")).toHaveCSS("line-height", "32px");
  await expect(story.locator(".story-frame")).toHaveCSS("padding", "32px");
  await expect(story.locator(".story-frame")).toHaveCSS("gap", "24px");

  const storyMetadata = story.locator(".source-sample > span");
  await expect(storyMetadata).toHaveCSS("font-size", "11px");
  await expect(storyMetadata).toHaveCSS("line-height", "16px");
  await expect(storyMetadata).toHaveCSS("letter-spacing", "1px");
});

test("wide landing uses only approved hero spacing", async ({ page }) => {
  await page.setViewportSize({ width: 1600, height: 1000 });
  await page.goto("/");
  await expect(page.locator(".landing-hero")).toHaveCSS("padding", "96px 0px 80px");
});

test("tablet landing switches to approved discrete spacing and type", async ({ page }) => {
  await page.setViewportSize({ width: 900, height: 1000 });
  await page.goto("/");
  const hero = page.locator(".landing-hero");
  await expect(hero).toHaveCSS("column-gap", "32px");
  await expect(hero.locator("h1")).toHaveCSS("font-size", "48px");
  await expect(hero.locator("h1")).toHaveCSS("line-height", "56px");
  await expect(page.locator(".story-step").first()).toHaveCSS("column-gap", "32px");
});

test("mobile shell keeps tokenized step geometry", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/announcement");

  const brand = page.getByRole("link", { name: "FINAL CHECK 홈" });
  await expect(brand).toHaveCSS("font-size", "20px");
  await expect(brand).toHaveCSS("line-height", "28px");

  const firstStep = page.getByRole("navigation", { name: "검사 단계" }).locator(".step").first();
  await expect(firstStep).toHaveCSS("padding", "12px 4px");
  await expect(firstStep).toHaveCSS("column-gap", "8px");
  await expect(firstStep).toHaveCSS("font-size", "12px");
  await expect(firstStep).toHaveCSS("line-height", "16px");
  await expect(firstStep.locator(".step-num")).toHaveCSS("width", "24px");
  await expect(firstStep.locator(".step-num")).toHaveCSS("height", "24px");
});

test("landing switches display typography at mobile without interpolated sizes", async ({ page }, info) => {
  test.skip(info.project.name !== "mobile");
  await page.goto("/");
  const hero = page.getByRole("heading", { level: 1, name: "제출 버튼을 누르기 전, 마지막 확인." });
  expect(["32px", "40px"]).toContain(await hero.evaluate(node => getComputedStyle(node).fontSize));
  expect(["40px", "48px"]).toContain(await hero.evaluate(node => getComputedStyle(node).lineHeight));
});

test("landing does not overflow the viewport", async ({ page }) => {
  await page.goto("/");
  expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)).toBe(false);
});
