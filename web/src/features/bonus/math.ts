/** Сколько баллов реально спишется: баланс, запрос и 50% суммы (копейки → баллы). */
export function clampRedeem(
  balancePoints: number,
  requestedPoints: number,
  totalKopeks: number,
): number {
  const cap = Math.floor((totalKopeks / 100) * 0.5);
  return Math.max(Math.min(balancePoints, requestedPoints, cap), 0);
}

/** Доля заполнения кольца/полосы уровня. */
export function levelProgress(
  lifetimeKopeks: number,
  toNextKopeks: number,
  hasNext: boolean,
): number {
  if (!hasNext) return 1;
  const total = lifetimeKopeks + toNextKopeks;
  if (total <= 0) return 0;
  return Math.min(1, Math.max(0, lifetimeKopeks / total));
}
