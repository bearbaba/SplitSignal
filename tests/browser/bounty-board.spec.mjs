import { test, expect } from "@playwright/test";

const maliciousWatch = (id) => ({
  id: String(id),
  funder: "0x1111111111111111111111111111111111111111",
  finder: "0x0000000000000000000000000000000000000000",
  left_url: "https://left.test/<svg/onload=window.__xss=1>",
  right_url: "https://right.test/<img/src=x/onerror=window.__xss=1>",
  field: "<img/src=x onerror=x=1>",
  amount: "10000000000000000",
  opened_at: 1700000000 + Number(id),
  deadline: Math.floor(Date.now() / 1000) + 86400 + Number(id),
  left_value: "<b>yes</b>",
  right_value: "<i>yes</i>",
  status: "OPEN",
  note: "<svg/onload=window.__xss=2>"
});

test.beforeEach(async ({ page }) => {
  await page.route("https://esm.sh/**", async route => {
    const url = route.request().url();
    if (url.includes("/chains")) {
      await route.fulfill({
        contentType: "application/javascript",
        body: "export const studionet = {};"
      });
      return;
    }

    await route.fulfill({
      contentType: "application/javascript",
      body: "export const createClient = () => ({});"
    });
  });

  await page.addInitScript(() => {
    window.__xss = 0;
    window.__SPLITSIGNAL_TEST_HOOK__ = {
      nextWatch: async () => 23,
      watch: async (id) => ({
        id: String(id),
        funder: "0x1111111111111111111111111111111111111111",
        finder: "0x0000000000000000000000000000000000000000",
        left_url: "https://left.test/<svg/onload=window.__xss=1>",
        right_url: "https://right.test/<img/src=x/onerror=window.__xss=1>",
        field: "<img/src=x onerror=x=1>",
        amount: "10000000000000000",
        opened_at: 1700000000 + Number(id),
        deadline: Math.floor(Date.now() / 1000) + 86400 + Number(id),
        left_value: "<b>yes</b>",
        right_value: "<i>yes</i>",
        status: "OPEN",
        note: "<svg/onload=window.__xss=2>"
      })
    };
  });
});

test("bounty board keeps refresh/pagination controls and renders contract data as text", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("button", { name: "Find Bounties" }).click();

  const pager = page.locator("#watchPager");
  await expect(pager).toBeVisible();
  await expect(page.locator("#watchPageInfo")).toHaveText("Page 1 of 3 · 22 Watches");
  await expect(page.locator("#prevWatches")).toBeDisabled();
  await expect(page.locator("#nextWatches")).toBeEnabled();

  const firstRow = page.locator(".watchrow").first();
  await expect(firstRow).toContainText("<img/src=x onerror=x=1>");
  await expect(firstRow).toContainText("https://left.test/<svg/onload=window.__xss=1>");

  await firstRow.locator("summary").click();
  await expect(firstRow.locator("dl")).toContainText("funder");
  await expect(firstRow.locator("dl")).toContainText("finder");
  await expect(firstRow.locator("dl")).toContainText("left_url");
  await expect(firstRow.locator("dl")).toContainText("right_url");
  await expect(firstRow.locator("dl")).toContainText("field");
  await expect(firstRow.locator("dl")).toContainText("amount");
  await expect(firstRow.locator("dl")).toContainText("opened_at");
  await expect(firstRow.locator("dl")).toContainText("deadline");
  await expect(firstRow.locator("dl")).toContainText("left_value");
  await expect(firstRow.locator("dl")).toContainText("right_value");
  await expect(firstRow.locator("dl")).toContainText("status");
  await expect(firstRow.locator("dl")).toContainText("note");

  await expect(page.locator("#huntList img")).toHaveCount(0);
  await expect(page.locator("#huntList svg")).toHaveCount(0);
  expect(await page.evaluate(() => window.__xss)).toBe(0);

  await page.locator("#nextWatches").click();
  await expect(page.locator("#watchPageInfo")).toHaveText("Page 2 of 3 · 22 Watches");
  await expect(pager).toBeVisible();
  await expect(page.locator("#prevWatches")).toBeEnabled();
  await expect(page.locator("#nextWatches")).toBeEnabled();

  await page.locator("#reloadHunt").click();
  await expect(page.locator("#watchPageInfo")).toHaveText("Page 2 of 3 · 22 Watches");
  await expect(pager).toBeVisible();
  await expect(page.locator("#prevWatches")).toBeEnabled();
  await expect(page.locator("#nextWatches")).toBeEnabled();
  expect(await page.evaluate(() => window.__xss)).toBe(0);
});
