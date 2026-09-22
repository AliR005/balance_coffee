import { describe, expect, it } from "vitest";
import { nextAction, sortBoard, urgencyOf } from "./features/barista/urgency";

const NOW = new Date("2026-09-22T09:00:00Z").getTime();

describe("urgencyOf", () => {
  it("считает минуты и просрочку", () => {
    expect(urgencyOf("2026-09-22T09:10:00Z", NOW)).toEqual({
      mins: 10,
      overdue: false,
      level: "normal",
    });
    expect(urgencyOf("2026-09-22T09:03:00Z", NOW).level).toBe("soon");
    expect(urgencyOf("2026-09-22T08:59:00Z", NOW)).toEqual({
      mins: -1,
      overdue: true,
      level: "overdue",
    });
  });
});

describe("sortBoard", () => {
  it("сортирует по времени подачи", () => {
    const orders = [
      { id: 3, pickup_at: "2026-09-22T09:30:00Z" },
      { id: 1, pickup_at: "2026-09-22T09:10:00Z" },
      { id: 2, pickup_at: "2026-09-22T09:10:00Z" },
    ];
    expect(sortBoard(orders).map((o) => o.id)).toEqual([1, 2, 3]);
  });
});

describe("nextAction", () => {
  it("одна большая кнопка на статус", () => {
    expect(nextAction("confirmed")).toEqual({ to: "preparing", label: "Принять" });
    expect(nextAction("preparing")).toEqual({ to: "ready", label: "Готово" });
    expect(nextAction("ready")).toEqual({ to: "picked_up", label: "Выдан" });
    expect(nextAction("picked_up")).toBeNull();
    expect(nextAction("cancelled")).toBeNull();
  });
});
