import path from "node:path";

import AxeBuilder from "@axe-core/playwright";
import { type Page, expect } from "@playwright/test";

export const FIXTURES = path.resolve(__dirname, "../../../engine/tests/fixtures/data");
export const PASSWORD = "Passw0rd!dev"; // local Keycloak test users only

/** Sign in through the real Keycloak page, like a user. */
export async function signIn(page: Page, user = "alice"): Promise<void> {
  await page.goto("/");
  await page.waitForURL(/\/realms\/driplytics\//, { timeout: 60_000 });
  await page.locator('input[name="username"]').fill(user);
  await page.locator('input[name="password"]').fill(PASSWORD);
  await page.locator('[type="submit"]').first().click();
  await page.waitForURL((url) => !url.pathname.startsWith("/realms/"), { timeout: 60_000 });
  await expect(page.getByRole("navigation", { name: "Main" })).toBeVisible();
}

/** No serious or critical WCAG 2.1 A/AA violations (axe-core). */
export async function expectAccessible(page: Page, label: string): Promise<void> {
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  const serious = results.violations
    .filter((v) => v.impact === "serious" || v.impact === "critical")
    .map((v) => `${v.id} (${v.impact}): ${v.help} → ${v.nodes.map((n) => n.target.join(" ")).slice(0, 3).join(", ")}`);
  expect(serious, `${label}: accessibility violations`).toEqual([]);
}
