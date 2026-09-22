const KEY = "balance-sound";

export function soundEnabled(): boolean {
  return localStorage.getItem(KEY) === "1";
}

export function setSoundEnabled(on: boolean): void {
  localStorage.setItem(KEY, on ? "1" : "0");
}

/** Короткий сигнал нового заказа через Web Audio (включается кнопкой — политики браузеров). */
export function playNewOrderSound(): void {
  if (!soundEnabled()) return;
  try {
    const Ctx = window.AudioContext;
    if (!Ctx) return;
    const ctx = new Ctx();
    const notes = [660, 880];
    notes.forEach((freq, i) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = freq;
      const t0 = ctx.currentTime + i * 0.18;
      gain.gain.setValueAtTime(0.001, t0);
      gain.gain.exponentialRampToValueAtTime(0.3, t0 + 0.03);
      gain.gain.exponentialRampToValueAtTime(0.001, t0 + 0.16);
      osc.connect(gain).connect(ctx.destination);
      osc.start(t0);
      osc.stop(t0 + 0.18);
    });
    window.setTimeout(() => void ctx.close(), 600);
  } catch {
    /* без звука — не блокируем доску */
  }
}
