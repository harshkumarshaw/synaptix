import { test, expect } from "@playwright/test";

test.describe("Electives Feature Flow", () => {
  test("student can rank and submit elective preferences", async ({ page }) => {
    // 1. Login as Student
    await page.goto("/login");
    const emailInput = page.locator('input[type="email"]');
    await emailInput.waitFor({ state: "visible", timeout: 10_000 });
    await emailInput.fill("student1@jmn.edu.in");
    await page.fill('input[type="password"]', "Synaptix@2026");
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/.*dashboard/);

    // 2. Navigate to Electives
    await page.click("text=Electives");
    await expect(page).toHaveURL(/.*electives/);
    await expect(page.getByText("Electives Portal")).toBeVisible();

    // 3. Switch between Block 1 and Block 2
    await page.click("button:has-text('Block 2')");
    await page.click("button:has-text('Block 1')");

    // 4. Try to click "+ Add" if any available electives exist
    const addButton = page
      .locator("text=Available Electives")
      .locator("..")
      .locator("button:has-text('+ Add')")
      .first();
    const hasAvailable = await addButton.isVisible();
    if (hasAvailable) {
      await addButton.click();
    }

    // 5. Submit Ranking List if enabled
    const submitBtn = page.getByRole("button", { name: /Submit/i });
    if (await submitBtn.isEnabled()) {
      await submitBtn.click();
      // Check for success toast
      await expect(
        page.getByText(/submitted successfully|preferences/i).first(),
      ).toBeVisible({ timeout: 15_000 });
    } else {
      // If disabled, check that they are already saved
      await expect(
        page.getByText(/are saved|My Choice Sequence/i).first(),
      ).toBeVisible();
    }
  });

  test("admin can run allocation algorithm in dry run and live mode", async ({
    page,
  }) => {
    // 1. Login as Admin
    await page.goto("/login");
    const emailInput2 = page.locator('input[type="email"]');
    await emailInput2.waitFor({ state: "visible", timeout: 10_000 });
    await emailInput2.fill("admin@jmn.edu.in");
    await page.fill('input[type="password"]', "Synaptix@2026");
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/.*dashboard/);

    // 2. Navigate to Electives
    await page.click("text=Electives");
    await expect(page).toHaveURL(/.*electives/);
    await expect(page.getByText("Electives Allocation Engine")).toBeVisible();

    // Wait for electives to load and populate the curriculum dropdown
    await expect(page.locator("select").first()).not.toContainText(
      "No curriculum found",
      { timeout: 15_000 },
    );

    // 3. Select algorithm
    const rankedRadio = page.locator("input[value='ranked']");
    if (await rankedRadio.isVisible()) {
      await rankedRadio.check();
    }

    // 4. Run Dry Run
    const dryRunBtn = page.getByRole("button", { name: /Dry Run/i });
    await expect(dryRunBtn).toBeEnabled();
    await dryRunBtn.click();

    // Verify dry run preview outputs with generous timeout for API execution
    await expect(page.getByText(/Allocation Results/i).first()).toBeVisible({
      timeout: 20_000,
    });
    await expect(page.getByText(/Simulation/i).first()).toBeVisible({
      timeout: 20_000,
    });

    // 5. Run Live Allocation
    const runBtn = page.getByRole("button", { name: /Run Live/i });
    await expect(runBtn).toBeEnabled();
    await runBtn.click();

    // Confirmation dialog check (if present)
    const confirmBtn = page.getByRole("button", { name: /Confirm/i });
    if (await confirmBtn.isVisible()) {
      await confirmBtn.click();
    }

    // Verify results
    await expect(page.getByText(/Total Considered/i)).toBeVisible({
      timeout: 20_000,
    });
    await expect(page.getByText(/Total Allocated/i)).toBeVisible({
      timeout: 20_000,
    });
  });
});
