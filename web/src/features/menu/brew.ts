import type { ProductOut } from "../../shared/api/generated/api";
import type { BrewVariant } from "../../shared/ui/BrewView";

/** Эвристика рисунка чашки по напитку (пока у API нет поля art). */
export function brewVariantOf(product: ProductOut): BrewVariant {
  if (/(matcha|cocoa|raf|mocha)/.test(product.slug)) return "full";
  if (/(tea|americano|espresso|cold-brew)/.test(product.slug)) return "crema";
  if (/(cappuccino|flat-white)/.test(product.slug)) return "tulip";
  return "heart";
}

const LIQUID_TOKENS = new Set(["cow", "lactose_free", "oat", "almond", "coconut", "milk"]);

/** visual {liquid} → токен цвета. */
export function milkToken(visual: unknown): string {
  if (typeof visual === "object" && visual !== null) {
    const liquid = (visual as Record<string, unknown>)["liquid"];
    if (typeof liquid === "string") {
      if (liquid === "cow" || liquid === "milk") return "var(--liquid-milk)";
      if (LIQUID_TOKENS.has(liquid))
        return `var(--liquid-${liquid === "lactose_free" ? "milk" : liquid})`;
    }
  }
  return "var(--liquid-milk)";
}

/** Токен цвета выбранного молока в позиции (для чашки на экране напитка). */
export function selectedMilkColor(product: ProductOut, optionIds: number[]): string {
  for (const g of product.groups ?? []) {
    if (g.key !== "milk") continue;
    for (const o of g.options ?? []) {
      if (optionIds.includes(o.id)) return milkToken(o.visual);
    }
  }
  return "var(--liquid-milk)";
}
