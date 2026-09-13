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
