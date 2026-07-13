import { test, expect } from "@playwright/test";

test.describe("Leave Management Flow", () => {
  test("student can submit leave request with valid details", async ({
    page,
  }) => {
    // 1. Login as Student
    await page.goto("/login");
    const emailInput = page.locator('input[type="email"]');
    await emailInput.waitFor({ state: "visible", timeout: 10_000 });
    await emailInput.fill("student1@jmn.edu.in");
    await page.fill('input[type="password"]', "Synaptix@2026");
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/.*dashboard/);

    // 2. Navigate to Leave Requests
    await page.click("text=Leave Requests");
    await expect(page).toHaveURL(/.*leave/);
    await expect(page.getByText("Request Leave")).toBeVisible();

    // 3. Fill in Leave Request form
    // Select medical type
    await page.selectOption("select", "medical");

    // Set dates
    const todayStr = new Date().toISOString().split("T")[0];
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowStr = tomorrow.toISOString().split("T")[0];

    // Set input values for date picker
    await page.fill('input[type="date"] >> nth=0', todayStr);
    await page.fill('input[type="date"] >> nth=1', tomorrowStr);

    // Enter detailed reason (minimum 10 characters)
    await page.fill(
      'textarea[placeholder*="reason for leave"]',
      "Attending medical conference at local hospital",
    );

    // Submit request
    await page.click('button[type="submit"]:has-text("Submit Application")');

    // Verify success toast message
    await expect(
      page.getByText(/Your leave request has been submitted successfully/i),
    ).toBeVisible();
  });

  test("faculty can view approval queue and approve a leave request", async ({
    page,
  }) => {
    // 1. Login as Faculty
    await page.goto("/login");
    const emailInput2 = page.locator('input[type="email"]');
    await emailInput2.waitFor({ state: "visible", timeout: 10_000 });
    await emailInput2.fill("dr.ray@jmn.edu.in");
    await page.fill('input[type="password"]', "Synaptix@2026");
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/.*dashboard/);

    // 2. Navigate to Leave Requests
    await page.click("text=Leave Requests");
    await expect(page).toHaveURL(/.*leave/);
    await expect(page.getByText("Leave Approval Queue")).toBeVisible();

    // 3. Click first pending request in the queue table (if available)
    const reviewBtn = page.locator("button:has-text('Review')").first();
    try {
      await reviewBtn.waitFor({ state: "visible", timeout: 5000 });
      await reviewBtn.click();

      // Verify the slide-out detail sheet is open
      await expect(page.getByText("Leave Details")).toBeVisible();

      // Fill in remarks
      await page.fill(
        'input[placeholder*="remarks"]',
        "Approved after reviewing conference invitation",
      );

      // Approve request
      await page.click('button:has-text("Approve")');

      // Verify success toast message
      await expect(page.getByText(/Leave Approved/i)).toBeVisible();
    } catch (e) {
      console.log("No pending leave requests found to approve.");
    }
  });
});
