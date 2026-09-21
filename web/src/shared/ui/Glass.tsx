import { useId } from "react";

/** Стакан со льдом и зёрнами для hero и старта (по preview.html: glass). Без самодвижения вне hero/start. */
export function Glass({
  label = "Холодный латте со льдом",
  className = "",
  animated = false,
}: {
  label?: string;
  className?: string;
  animated?: boolean;
}) {
  const uid = useId().replace(/[^a-zA-Z0-9]/g, "");
  const clip = `glass-${uid}`;
  const bean = (x: number, y: number, r: number, s: number, c: string) => (
    <g className={`fl ${c}`}>
      <g transform={`translate(${x} ${y}) rotate(${r}) scale(${s})`}>
        <ellipse rx="12" ry="17" fill="var(--liquid-coffee-strong)" />
        <path
          d="M0 -15C7 -5 -7 5 0 15"
          stroke="var(--bg)"
          strokeWidth="2.4"
          fill="none"
          strokeLinecap="round"
        />
      </g>
    </g>
  );
  return (
    <svg
      viewBox="0 0 320 470"
      role="img"
      aria-label={label}
      className={`${animated ? "glass-anim" : ""} ${className}`}
    >
      <defs>
        <clipPath id={clip}>
          <path d="M70 62H250L232 414Q230 436 208 436H112Q90 436 88 414Z" />
        </clipPath>
        <linearGradient id={`liq-${uid}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="var(--liquid-milk)" />
          <stop offset=".28" stopColor="var(--liquid-oat)" />
          <stop offset=".55" stopColor="var(--syrup-caramel)" />
          <stop offset=".8" stopColor="var(--liquid-coffee)" />
          <stop offset="1" stopColor="var(--liquid-coffee-strong)" />
        </linearGradient>
      </defs>
      {bean(34, 130, -30, 1.1, "f2")}
      {bean(290, 88, 40, 0.8, "f3")}
      {bean(300, 330, -20, 1.2, "f4")}
      {bean(28, 320, 25, 0.9, "f5")}
      <g clipPath={`url(#${clip})`}>
        <rect x="60" y="52" width="200" height="392" fill={`url(#liq-${uid})`} />
        <g className="ice i1">
          <rect
            x="96"
            y="96"
            width="66"
            height="62"
            rx="14"
            transform="rotate(-14 129 127)"
            fill="var(--liquid-coconut)"
            opacity=".55"
          />
        </g>
        <g className="ice i2">
          <rect
            x="168"
            y="128"
            width="58"
            height="56"
            rx="13"
            transform="rotate(12 197 156)"
            fill="var(--liquid-coconut)"
            opacity=".4"
          />
        </g>
        <g className="ice i3">
          <rect
            x="112"
            y="214"
            width="60"
            height="58"
            rx="13"
            transform="rotate(8 142 243)"
            fill="var(--liquid-coconut)"
            opacity=".35"
          />
        </g>
        <g className="ice i4">
          <rect
            x="170"
            y="262"
            width="52"
            height="50"
            rx="12"
            transform="rotate(-10 196 287)"
            fill="var(--liquid-coconut)"
            opacity=".3"
          />
        </g>
      </g>
      <path
        d="M70 62H250L232 414Q230 436 208 436H112Q90 436 88 414Z"
        fill="none"
        stroke="var(--text)"
        strokeWidth="2"
        opacity=".28"
      />
      <ellipse
        cx="160"
        cy="62"
        rx="90"
        ry="8"
        fill="none"
        stroke="var(--text)"
        strokeWidth="2"
        opacity=".3"
      />
      {bean(258, 44, 15, 1, "f1")}
    </svg>
  );
}
