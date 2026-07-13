import { test, expect } from "@playwright/test";

// Reusable login helper
async function loginAs(page, email: string) {
  await page.goto("/login");
  const emailInput = page.locator('input[type="email"]');
  await emailInput.waitFor({ state: "visible", timeout: 10_000 });
  await emailInput.fill(email);
  await page.fill('input[type="password"]', "Synaptix@2026");
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/.*dashboard/);
}

test.describe("Attendance Flow", () => {
  test("faculty can view mark attendance page", async ({ page }) => {
    await loginAs(page, "dr.ray@jmn.edu.in");

    await page.click("text=Mark Attendance");
    await expect(page).toHaveURL(/.*attendance/);
    await expect(
      page.getByRole("heading", { name: "Mark Attendance" }),
    ).toBeVisible();
  });

  test("student can view attendance summary", async ({ page }) => {
    await loginAs(page, "student1@jmn.edu.in");

    await page.click("text=My Attendance");
    await expect(page).toHaveURL(/.*attendance/);
    // Student attendance displays details
    await expect(
      page.getByText(/Anatomy|Physiology|Biochemistry/i).first(),
    ).toBeVisible();
  });

  test("student dashboard shows attendance percentage", async ({ page }) => {
    await loginAs(page, "student1@jmn.edu.in");

    // Dashboard should display some percentage metric
    await expect(page.getByText(/%/).first()).toBeVisible();
  });
});
