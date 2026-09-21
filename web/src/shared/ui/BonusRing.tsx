import { useEffect, useRef, useState } from "react";
import { useReducedMotion, useVisible } from "../lib/useVisible";

interface Props {
  balance: number;
  /** Доля заполнения 0..1. */
  progress?: number;
  label?: string;
}

/** Бонусное кольцо 210px: заполняется при появлении, число считается от 0. */
export function BonusRing({ balance, progress = 0.68, label = "баллов" }: Props) {
  const [ref, visible] = useVisible<HTMLDivElement>();
  const reduced = useReducedMotion();
  const [shown, setShown] = useState(0);
  const started = useRef(false);

  useEffect(() => {
    if (!visible || started.current) return;
    started.current = true;
    if (reduced) {
      setShown(balance);
      return;
    }
    const t0 = performance.now();
    let raf = 0;
    const tick = (now: number) => {
      const k = Math.min(1, (now - t0) / 1600);
      setShown(Math.round(balance * (1 - Math.pow(1 - k, 3))));
      if (k < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [visible, balance, reduced]);

  const target = 452 * (1 - Math.min(1, Math.max(0, progress)));

  return (
    <div
      ref={ref}
      className={`relative mx-auto h-[210px] w-[210px] ${visible ? "bonus-ring-go" : ""}`}
    >
      <svg viewBox="0 0 170 170" aria-hidden className="h-full w-full -rotate-90">
        <defs>
          <linearGradient id="bonus-ring-g" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="var(--primary)" />
            <stop offset="1" stopColor="var(--accent)" />
          </linearGradient>
        </defs>
        <circle cx="85" cy="85" r="72" fill="none" strokeWidth="10" stroke="var(--surface-3)" />
        <circle
          cx="85"
          cy="85"
          r="72"
          fill="none"
          strokeWidth="10"
          strokeLinecap="round"
          stroke="url(#bonus-ring-g)"
          className="bonus-ring-fill"
          style={{ "--ring-target": target } as React.CSSProperties}
        />
      </svg>
      <div className="absolute inset-0 grid place-content-center text-center">
        <b className="tabular text-5xl leading-none font-semibold">{shown}</b>
        <span className="mt-1 text-[13px] text-text-2">{label}</span>
      </div>
    </div>
  );
}
