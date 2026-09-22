/** Срочность подачи: минуты до pickup, просрочка, уровень. Чистые функции (тестируются). */

export type UrgencyLevel = "overdue" | "soon" | "normal";

export interface Urgency {
  mins: number;
  overdue: boolean;
  level: UrgencyLevel;
}

export function urgencyOf(pickupIso: string, nowMs: number): Urgency {
  const mins = Math.round((new Date(pickupIso).getTime() - nowMs) / 60_000);
  if (mins < 0) return { mins, overdue: true, level: "overdue" };
  if (mins < 5) return { mins, overdue: false, level: "soon" };
  return { mins, overdue: false, level: "normal" };
}

/** Сортировка доски: сначала просроченные и ближайшие по времени подачи. */
export function sortBoard<T extends { pickup_at: string; id: number }>(orders: T[]): T[] {
  return [...orders].sort((a, b) => {
    const d = new Date(a.pickup_at).getTime() - new Date(b.pickup_at).getTime();
    return d !== 0 ? d : a.id - b.id;
  });
}

export function nextAction(status: string): { to: string; label: string } | null {
  if (status === "confirmed") return { to: "preparing", label: "Принять" };
  if (status === "preparing") return { to: "ready", label: "Готово" };
  if (status === "ready") return { to: "picked_up", label: "Выдан" };
  return null;
}
