import { useEffect } from "react";

/** Экран не гаснет, где поддерживается Wake Lock. */
export function useWakeLock(active: boolean): void {
  useEffect(() => {
    if (!active) return;
    let lock: { release: () => Promise<void> } | null = null;
    let cancelled = false;
    const nav = navigator as Navigator & {
      wakeLock?: { request: (kind: string) => Promise<{ release: () => Promise<void> }> };
    };
    if (nav.wakeLock) {
      nav.wakeLock
        .request("screen")
        .then((l) => {
          if (cancelled) void l.release();
          else lock = l;
        })
        .catch(() => {});
    }
    return () => {
      cancelled = true;
      if (lock) void lock.release();
    };
  }, [active]);
}
