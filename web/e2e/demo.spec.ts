import { expect, test } from "@playwright/test";

/** Сквозное демо: клиент заказал → бариста принял → клиент увидел статус. */
test("client orders, barista accepts, client sees status", async ({ page }) => {
  const apiErrors: string[] = [];
  page.on("pageerror", (e) => apiErrors.push(String(e).slice(0, 200)));
  const customer = `E2E-${Date.now() % 100000}`;

  // Клиент: старт → меню → напиток → в заказ.
  await page.goto("/");
  await page.getByRole("button", { name: "Заказать" }).click();
  await page.waitForURL("**/menu");
  await page.locator("article button[aria-label^='Добавить']").first().click();
  await page.waitForURL("**/drink/*");
  await page.getByRole("button", { name: /Добавить в заказ/ }).click();

  // Оформление.
  await page.goto("/checkout");
  await page.getByPlaceholder("Как к вам обращаться").fill(customer);
  await page.getByPlaceholder("+7 ___ ___-__-__").fill("+7 900 000-00-99");
  await page.waitForTimeout(1500);
  await page.getByRole("button", { name: /^Заказать/ }).click();
  await page.waitForURL("**/orders*", { timeout: 15000 });
  const orderId = page.url().match(/fresh=(\d+)/)?.[1];
  expect(orderId).toBeTruthy();

  // Бариста: вход и принятие заказа.
  await page.goto("/staff");
  await page.getByRole("combobox").selectOption({ index: 1 });
  await page.getByLabel("PIN", { exact: false }).fill("1234");
  await page.getByRole("button", { name: "Войти" }).click();
  await page.waitForURL("**/staff/board", { timeout: 10000 });
  const card = page.locator("article", { hasText: customer });
  await expect(card).toBeVisible({ timeout: 10000 });
  await card.getByRole("button", { name: "Принять" }).click();
  await expect(card.getByRole("button", { name: "Готово" })).toBeVisible({ timeout: 10000 });

  // Клиент видит новый статус без перезагрузки (SSE/опрос).
  await page.goto(`/orders?fresh=${orderId}`);
  await expect(page.getByText("Готовим ваш кофе")).toBeVisible({ timeout: 20000 });

  expect(apiErrors).toEqual([]);
});
