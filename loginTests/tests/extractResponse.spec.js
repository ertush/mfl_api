import { test, expect } from "@playwright/test";
import fs from "fs";

test("response", async ({ page }) => {
  await page.goto("http://admin.kmhfltest.health.go.ke");
  await page.getByRole("link", { name: "Log in" }).click();

  await page.getByPlaceholder("you@geemail.com").click();
  await page.getByPlaceholder("you@geemail.com").fill("test@mflcountyuser.com");
  await page.getByPlaceholder("you@geemail.com").press("Tab");
  await page.getByPlaceholder("*********").fill("county@1234");
  await page.getByRole("button", { name: "Log in" }).click();

  // Wait for the response that contains the access token
  const response = await page.waitForResponse(
    (response) =>
      response.url().includes("oauth/token") && response.status() === 200
  );

  // Extract the response body as a JSON object
  const responseBody = await response.json();

  // Save the response body to a JSON file
  const jsonData = JSON.stringify(responseBody, null, 2);
  fs.writeFileSync("response.json", jsonData);
});
