import { test, expect } from "@playwright/test";

test.describe("Navigation Flow", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    const emailInput = page.locator('input[type="email"]');
    await emailInput.waitFor({ state: "visible", timeout: 10_000 });
    await emailInput.fill("admin@jmn.edu.in");
    await page.fill('input[type="password"]', "Synaptix@2026");
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/.*dashboard/);
  });

  const pages = [
    { nav: "Attendance", url: /.*attendance/ },
    { nav: "Logbook", url: /.*logbook/ },
    { nav: "DOAP Skills", url: /.*doap/ },
    { nav: "Electives", url: /.*electives/ },
    { nav: "Leave Requests", url: /.*leave/ },
  ];

  for (const p of pages) {
    test(`navigate to ${p.nav}`, async ({ page }) => {
      await page.click(`text=${p.nav}`);
      await expect(page).toHaveURL(p.url);
    });
  }
});
