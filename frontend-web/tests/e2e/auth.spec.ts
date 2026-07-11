import { test, expect } from "@playwright/test";

test.describe("Authentication Flow", () => {
  test("login with valid credentials redirects to dashboard", async ({
    page,
  }) => {
    await page.goto("/login");

    const emailInput = page.locator('input[type="email"]');
    await emailInput.waitFor({ state: "visible", timeout: 10_000 });
    await emailInput.fill("admin@jmn.edu.in");
    await page.fill('input[type="password"]', "Synaptix@2026");
    await page.click('button[type="submit"]');

    // Wait for URL redirect to /dashboard
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(
      page.getByRole("heading", { name: "Dashboard" }),
    ).toBeVisible();
  });

  test("login with invalid credentials shows error", async ({ page }) => {
    await page.goto("/login");

    const emailInput = page.locator('input[type="email"]');
    await emailInput.waitFor({ state: "visible", timeout: 10_000 });
    await emailInput.fill("wrong@jmn.edu.in");
    await page.fill('input[type="password"]', "wrongpassword");
    await page.click('button[type="submit"]');

    // Should display invalid / failed error message
    await expect(page.getByText(/invalid|failed/i).first()).toBeVisible();
    await expect(page).toHaveURL(/.*login/);
  });

  test("accessing dashboard without login redirects to login", async ({
    page,
  }) => {
    // Clear localStorage to ensure user is logged out
    await page.goto("/login");
    await page.evaluate(() => localStorage.clear());

    await page.goto("/dashboard");
    await expect(page).toHaveURL(/.*login/);
  });
});
