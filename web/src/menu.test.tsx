import { describe, expect, it } from "vitest";
import type { ProductOut } from "./shared/api/generated/api";
import { useCart } from "./features/cart/store";
import {
  bonusPreview,
  computePrice,
  defaultSelection,
  missingRequiredGroups,
  selectionDeltas,
} from "./features/menu/pricing";

const product = {
  id: 7,
  base_price: 32000,
  groups: [
    {
      id: 1,
      key: "size",
      name: "Размер",
      min_select: 1,
      max_select: 1,
      required: true,
      default_option_ids: [2],
      options: [
        { id: 1, name: "S", price_delta: -3000, available: true },
        { id: 2, name: "M", price_delta: 0, available: true },
        { id: 3, name: "L", price_delta: 6000, available: true },
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
      options: [
        { id: 10, name: "Ваниль", price_delta: 4000, available: true },
        { id: 11, name: "Карамель", price_delta: 4000, available: false },
      ],
    },
  ],
} as unknown as ProductOut;

describe("computePrice (SPEC 5.1)", () => {
  it("без опций", () => {
    expect(computePrice(32000, [], 1)).toBe(32000);
  });
  it("с опциями", () => {
    expect(computePrice(32000, [5000, 4000], 1)).toBe(41000);
  });
  it("отрицательная дельта", () => {
    expect(computePrice(32000, [-3000], 1)).toBe(29000);
  });
  it("количество", () => {
    expect(computePrice(32000, [5000], 2)).toBe(74000);
  });
  it("не ниже нуля", () => {
    expect(computePrice(1000, [-5000], 1)).toBe(0);
  });
});

describe("selection helpers", () => {
  it("deltas по снапшоту продукта", () => {
    expect(selectionDeltas(product, [1, 10])).toEqual([-3000, 4000]);
  });
  it("дефолты из API", () => {
    expect(defaultSelection(product)).toEqual({ 1: [2] });
  });
  it("обязательная группа блокирует добавление", () => {
    expect(missingRequiredGroups(product, {})).toEqual([1]);
    expect(missingRequiredGroups(product, { 1: [2] })).toEqual([]);
  });
  it("бонус-превью 5% от рублей, вниз", () => {
    expect(bonusPreview(32000)).toBe(16);
  });
});

describe("cart store", () => {
  it("добавляет и объединяет одинаковые позиции", () => {
    useCart.setState({ locationId: null, items: [] });
    const { addItem } = useCart.getState();
    addItem(1, { productId: 7, optionIds: [2], qty: 1 });
    addItem(1, { productId: 7, optionIds: [2], qty: 2 });
    expect(useCart.getState().items).toHaveLength(1);
    expect(useCart.getState().items[0]?.qty).toBe(3);
  });

  it("разные опции — разные позиции", () => {
    useCart.setState({ locationId: null, items: [] });
    const { addItem } = useCart.getState();
    addItem(1, { productId: 7, optionIds: [2], qty: 1 });
    addItem(1, { productId: 7, optionIds: [3], qty: 1 });
    expect(useCart.getState().items).toHaveLength(2);
  });

  it("смена точки с заказом блокируется без clear", () => {
    useCart.setState({ locationId: null, items: [] });
    const s = useCart.getState();
    s.addItem(1, { productId: 7, optionIds: [2], qty: 1 });
    s.setLocation(2);
    expect(useCart.getState().locationId).toBe(1);
    s.setLocation(2, { clear: true });
    expect(useCart.getState().locationId).toBe(2);
    expect(useCart.getState().items).toHaveLength(0);
  });
});
