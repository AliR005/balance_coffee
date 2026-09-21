import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface CartItem {
  productId: number;
  optionIds: number[];
  qty: number;
}

interface CartState {
  locationId: number | null;
  items: CartItem[];
  /** Ключ позиции: продукт + отсортированные опции. */
  addItem: (locationId: number, item: CartItem) => void;
  setQty: (index: number, qty: number) => void;
  removeAt: (index: number) => void;
  /** Смена точки: с непустым заказом — только через подтверждение (чистит корзину). */
  setLocation: (locationId: number, opts?: { clear?: boolean }) => void;
  clear: () => void;
  count: () => number;
}

const keyOf = (item: CartItem) =>
  `${item.productId}:${[...item.optionIds].sort((a, b) => a - b).join(",")}`;

export const useCart = create<CartState>()(
  persist(
    (set, get) => ({
      locationId: null,
      items: [],
      addItem: (locationId, item) =>
        set((s) => {
          if (s.locationId !== null && s.locationId !== locationId && s.items.length > 0) return s;
          const items = [...s.items];
          const idx = items.findIndex((i) => keyOf(i) === keyOf(item));
          if (idx >= 0 && items[idx])
            items[idx] = { ...items[idx], qty: Math.min(10, items[idx].qty + item.qty) };
          else items.push(item);
          return { locationId, items };
        }),
      setQty: (index, qty) =>
        set((s) => ({
          items: s.items.map((i, k) =>
            k === index ? { ...i, qty: Math.min(10, Math.max(1, qty)) } : i,
          ),
        })),
      removeAt: (index) => set((s) => ({ items: s.items.filter((_, k) => k !== index) })),
      setLocation: (locationId, opts) =>
        set((s) => {
          if (s.locationId === locationId) return s;
          if (s.items.length > 0 && !opts?.clear) return s;
          return { locationId, items: [] };
        }),
      clear: () => set({ items: [] }),
      count: () => get().items.reduce((a, i) => a + i.qty, 0),
    }),
    { name: "balance-cart" },
  ),
);

/** Флаг первого запуска (стартовый экран показывается один раз). */
export function hasSeenWelcome(): boolean {
  return localStorage.getItem("balance-welcome") === "1";
}

export function markWelcomeSeen(): void {
  localStorage.setItem("balance-welcome", "1");
}
