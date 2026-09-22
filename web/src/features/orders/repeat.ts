import type { MenuOut, OrderItemOut } from "../../shared/api/generated/api";
import type { CartItem } from "../cart/store";

export interface RebuildResult {
  ok: CartItem[];
  /** Названия позиций, которые недоступны и убраны. */
  dropped: string[];
}

/**
 * Повтор заказа по актуальному меню: недоступное убирается с явным сообщением.
 * Проверяет продукт, наличие опций и обязательные группы.
 */
export function rebuildOrder(menu: MenuOut, items: OrderItemOut[]): RebuildResult {
  const all = (menu.categories ?? []).flatMap((c) => c.products ?? []);
  const ok: CartItem[] = [];
  const dropped: string[] = [];

  for (const item of items) {
    const prod = all.find((p) => p.id === item.product_id);
    if (!prod || prod.available === false) {
      dropped.push(item.product_name);
      continue;
    }
    // Снапшот хранит названия, а не id — сопоставляем по названиям опций.
    const wantedNames = new Set((item.options ?? []).map((o) => (o as { option?: string }).option));
    const optionIds: number[] = [];
    let valid = true;
    for (const g of prod.groups ?? []) {
      const chosen = (g.options ?? []).filter((o) => wantedNames.has(o.name));
      const available = chosen.filter((o) => o.available !== false);
      if (available.length < chosen.length) {
        valid = false;
        break;
      }
      if (chosen.length < g.min_select) {
        valid = false;
        break;
      }
      optionIds.push(...chosen.slice(0, Math.max(g.max_select, 1)).map((o) => o.id));
    }
    if (!valid) {
      dropped.push(prod.name);
      continue;
    }
    ok.push({ productId: prod.id, optionIds, qty: Math.min(item.quantity, 10) });
  }

  return { ok, dropped };
}
