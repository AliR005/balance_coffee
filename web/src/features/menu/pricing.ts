import type { ProductOut } from "../../shared/api/generated/api";

/** Тот же алгоритм, что SPEC 5.1 на сервере: unit = base + deltas; line = unit × qty. */
export function computePrice(basePrice: number, deltas: number[], qty: number): number {
  return Math.max(basePrice + deltas.reduce((a, b) => a + b, 0), 0) * qty;
}

/** Дельты выбранных опций по снапшоту продукта из меню. */
export function selectionDeltas(product: ProductOut, optionIds: number[]): number[] {
  const deltaById = new Map<number, number>();
  for (const g of product.groups ?? [])
    for (const o of g.options ?? []) deltaById.set(o.id, o.price_delta);
  return optionIds.map((id) => deltaById.get(id) ?? 0);
}

/** Группы, где обязательный выбор не сделан (для подсветки). */
export function missingRequiredGroups(
  product: ProductOut,
  selection: Record<number, number[]>,
): number[] {
  return (product.groups ?? [])
    .filter((g) => {
      const min = g.min_select;
      if (min < 1) return false;
      const chosen = (selection[g.id] ?? []).length;
      return chosen < min;
    })
    .map((g) => g.id);
}

/** Начальный выбор: дефолты из API, иначе первый доступный вариант обязательных групп. */
export function defaultSelection(product: ProductOut): Record<number, number[]> {
  const sel: Record<number, number[]> = {};
  for (const g of product.groups ?? []) {
    const options = g.options ?? [];
    const availableDefaults = (g.default_option_ids ?? []).filter((id) =>
      options.some((o) => o.id === id && o.available),
    );
    if (availableDefaults.length > 0) {
      sel[g.id] = availableDefaults.slice(0, Math.max(g.max_select, 1));
    } else if (g.min_select >= 1) {
      const first = options.find((o) => o.available);
      if (first) sel[g.id] = [first.id];
    }
  }
  return sel;
}

/** Прогноз бонусов по SPEC 10.3: 5% от суммы в рублях, вниз (копейки → рубли → 5%). */
export function bonusPreview(totalKopeks: number): number {
  return Math.floor((totalKopeks / 100) * 0.05);
}
