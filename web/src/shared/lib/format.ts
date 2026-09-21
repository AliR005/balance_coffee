const rubFmt = new Intl.NumberFormat("ru-RU");

/** Копейки → «320 ₽». Деньги всегда int минорных единиц. */
export function formatRub(kopeks: number): string {
  return rubFmt.format(Math.round(kopeks / 100)) + "\u00a0₽";
}

/** 9 → «0:09». */
export function formatDuration(totalSec: number): string {
  const s = Math.max(0, Math.round(totalSec));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}
