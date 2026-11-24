/**
 * The Phase 0 exit demo, automated: sign in → upload historian_long.csv with its tag mapping →
 * watch the import → read the report (the accounting equation, the unmapped-tag banner, reasons,
 * the rejected-examples CSV).
 */
import path from "node:path";

import { expect, test } from "@playwright/test";

import { FIXTURES, expectAccessible, signIn } from "./helpers";

test("upload an export and read its import report", async ({ page }) => {
  await signIn(page);

  await page.getByRole("link", { name: "Imports", exact: true }).click();
  await page.getByRole("link", { name: "Upload export", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Upload a historian export" })).toBeVisible();
  await expectAccessible(page, "upload screen");

  // 1. Pick the export: the browser previews it before anything is uploaded.
  await page.locator('input[type="file"]').first().setInputFiles(path.join(FIXTURES, "historian_long.csv"));
  await expect(page.getByText("Long format (one row per tag and time)")).toBeVisible();
  await expect(page.getByRole("cell", { name: "FIT-101.PV" }).first()).toBeVisible();

  // 2. Add the tag mapping, then start.
  await page.locator('input[type="file"][accept=".csv"]').setInputFiles(path.join(FIXTURES, "tag_mapping.csv"));
  await expect(page.getByText("tag_mapping.csv", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Start import" }).click();

  // 3. The report page follows the import, then shows the ledger.
  await page.waitForURL(/\/data\/imports\/[0-9a-f-]{36}$/, { timeout: 60_000 });
  await expect(page.getByText("5,179 = 5,157 accepted + 19 rejected + 3 duplicates")).toBeVisible({
    timeout: 120_000,
  });
  await expect(page.getByText("Scoring is blocked: 1 unmapped tag")).toBeVisible();
  await expect(page.getByText("XV-999.PV", { exact: true })).toBeVisible();

  // Rejection reasons, with example rows on demand.
  await expect(page.getByRole("cell", { name: /Bad quality/ })).toBeVisible();
  await page.getByRole("button", { name: /4 examples/ }).click();
  await expect(page.getByText("Row in file")).toBeVisible();

  // Clock changes are explained in plain words.
  await expect(page.getByText(/Clocks went back: 4,315 values/)).toBeVisible();

  // The rejected examples download through the same-origin proxy.
  const download = page.waitForEvent("download");
  await page.getByRole("link", { name: /Rejected examples \(CSV\)/ }).click();
  expect((await download).suggestedFilename()).toMatch(/^rejected-.*\.csv$/);

  await expectAccessible(page, "import report");
});

test("main pages have no serious accessibility problems, in light and dark", async ({ page }) => {
  await signIn(page);
  for (const theme of ["light", "dark"]) {
    await page.evaluate((t) => localStorage.setItem("dl-theme", t), theme);
    for (const url of ["/", "/data/imports", "/data/tag-mapping", "/findings"]) {
      await page.goto(url);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
      await expectAccessible(page, `${url} (${theme})`);
    }
  }
});

test("signed-out visitors are sent to sign in, and the API proxy refuses them", async ({ page, request }) => {
  await page.goto("/data/imports");
  await expect(page).toHaveURL(/\/realms\/driplytics\//);
  const api = await request.get("/api/v1/me");
  expect(api.status()).toBe(401);
});
