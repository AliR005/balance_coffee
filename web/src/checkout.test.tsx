import { describe, expect, it } from "vitest";
import { newIdempotencyKey } from "./features/checkout/api";
import { isPhoneValid } from "./features/checkout/customer";
import { shouldSplash } from "./features/orders/registry";
import { rebuildOrder } from "./features/orders/repeat";
import type { MenuOut, OrderItemOut } from "./shared/api/generated/api";

const menu = {
  categories: [
    {
      id: 1,
      slug: "classic",
      name: "Классика",
      products: [
        {
          id: 7,
          slug: "latte",
          name: "Латте",
          base_price: 34000,
          available: true,
          groups: [
            {
              id: 1,
              key: "size",
              name: "Размер",
              min_select: 1,
              max_select: 1,
              required: true,
              default_option_ids: [],
              options: [
                { id: 2, name: "M", price_delta: 0, available: true },
                { id: 3, name: "L", price_delta: 6000, available: false },
              ],
            },
            {
              id: 4,
              key: "syrup",
              name: "Сироп",
              min_select: 0,
              max_select: 2,
              required: false,
              default_option_ids: [],
              options: [{ id: 10, name: "Ваниль", price_delta: 4000, available: true }],
            },
          ],
        },
        {
          id: 9,
          slug: "cold-brew",
          name: "Колд брю",
          base_price: 34000,
          available: false,
          groups: [],
        },
      ],
    },
  ],
} as unknown as MenuOut;

describe("idempotency key", () => {
  it("уникален на каждое открытие экрана", () => {
    expect(newIdempotencyKey()).not.toBe(newIdempotencyKey());
  });
});

describe("phone validation", () => {
  it("принимает нормальный номер", () => {
    expect(isPhoneValid("+7 900 123-45-67")).toBe(true);
  });
  it("отклоняет короткий", () => {
    expect(isPhoneValid("123")).toBe(false);
    expect(isPhoneValid("")).toBe(false);
  });
});

describe("rebuildOrder", () => {
  it("собирает доступное, убирает недоступное", () => {
    const items = [
      {
        product_id: 7,
        product_name: "Латте",
        quantity: 1,
        options: [{ group: "size", option: "M", price_delta: 0 }],
      },
      { product_id: 9, product_name: "Колд брю", quantity: 1, options: [] },
    ] as unknown as OrderItemOut[];
    const { ok, dropped } = rebuildOrder(menu, items);
    expect(ok).toHaveLength(1);
    expect(ok[0]?.productId).toBe(7);
    expect(dropped).toEqual(["Колд брю"]);
  });

  it("убирает позицию с недоступной обязательной опцией", () => {
    const items = [
      {
        product_id: 7,
        product_name: "Латте",
        quantity: 1,
        options: [{ group: "size", option: "L", price_delta: 6000 }],
      },
    ] as unknown as OrderItemOut[];
    const { ok, dropped } = rebuildOrder(menu, items);
    expect(ok).toHaveLength(0);
    expect(dropped).toEqual(["Латте"]);
  });
});

describe("splash once", () => {
  it("показывается один раз на заказ", () => {
    const id = 900001;
    sessionStorage.clear();
    expect(shouldSplash(id)).toBe(true);
    expect(shouldSplash(id)).toBe(false);
  });
});
