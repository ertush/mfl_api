import { test, expect } from "@playwright/test";
import fs from "fs";

test("json", async ({ page }) => {
  await page.goto("http://admin.kmhfltest.health.go.ke");
  await page.getByRole("link", { name: "Log in" }).click();
  await page.getByPlaceholder("you@geemail.com").click();
  await page.getByPlaceholder("you@geemail.com").fill("test@mflcountyuser.com");
  await page.getByPlaceholder("you@geemail.com").press("Tab");
  await page.getByPlaceholder("*********").fill("county@1234");
  await page.getByRole("button", { name: "Log in" }).click();

  //   // Assert that an access token is returned
  //   const response = await page.waitForResponse(
  //     (response) =>
  //       response.url().includes("oauth/login") && response.status() === 200
  //   );
  //   const responseBody = await response.json();
  //   expect(responseBody.access_token).toBeTruthy();

  //   // Save the response
  //   fs.writeFileSync("response.json", JSON.stringify(responseBody));
  if (page.isClosed()) {
    throw new Error("Page is closed");
  } else {
    // Wait for the response that contains the access token
    const response = await page.waitForResponse(
      (response) =>
        response.url().includes("oauth/login") && response.status() === 200
    );

    // Extract the access token from the response body
    const responseBody = await response.json();
    const accessToken = responseBody.access_token;

    // Save the access token to a JSON file
    const data = { access_token: accessToken };
    const jsonData = JSON.stringify(data, null, 2);
    fs.writeFileSync("response.json", jsonData);
  }
});
