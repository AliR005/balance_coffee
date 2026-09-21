import { useId } from "react";
import { useReducedMotion, useVisible } from "../lib/useVisible";

export type BrewVariant = "heart" | "tulip" | "full" | "crema";

interface Props {
  variant?: BrewVariant;
  /** Цвет молока/пены — только токен, напр. "var(--liquid-oat)". */
  milkColor?: string;
  durationSec?: number;
  paused?: boolean;
  title?: string;
  className?: string;
}

const HEART_PATH =
  "M100 132C58 104 60 62 84 62C94 62 100 70 100 76C100 70 106 62 116 62C140 62 142 104 100 132Z";

function Art({ variant }: { variant: BrewVariant }) {
  const stroke = "rgba(110,64,32,.38)";
  if (variant === "heart") {
    return (
      <g className="pop">
        <path d={HEART_PATH} fill="var(--m)" />
        <g transform="translate(100 97) scale(.62) translate(-100 -97)">
          <path d={HEART_PATH} fill="none" stroke={stroke} strokeWidth="2.4" />
        </g>
        <g transform="translate(100 97) scale(.3) translate(-100 -97)">
          <path d={HEART_PATH} fill="none" stroke={stroke} strokeWidth="3" />
        </g>
      </g>
    );
  }
  if (variant === "tulip") {
    const st = { fill: "var(--m)", stroke, strokeWidth: 3 };
    return (
      <>
        <g className="pop">
          <g transform="translate(100 112) scale(.52) translate(-100 -97)">
            <path d={HEART_PATH} {...st} />
          </g>
        </g>
        <g className="pop p2">
          <g transform="translate(100 91) scale(.42) translate(-100 -97)">
            <path d={HEART_PATH} {...st} />
          </g>
        </g>
        <g className="pop p3">
          <g transform="translate(100 73) scale(.32) translate(-100 -97)">
            <path d={HEART_PATH} {...st} />
          </g>
        </g>
      </>
    );
  }
  if (variant === "full") {
    return (
      <>
        <circle className="pool" cx="100" cy="100" r="57" fill="var(--m)" />
        <g className="pop">
          <circle cx="82" cy="84" r="3" fill="var(--accent)" opacity=".55" />
          <circle cx="118" cy="92" r="2.4" fill="var(--accent)" opacity=".55" />
          <circle cx="96" cy="118" r="3.2" fill="var(--accent)" opacity=".55" />
          <circle cx="124" cy="116" r="2" fill="var(--accent)" opacity=".55" />
          <circle cx="76" cy="108" r="2.2" fill="var(--accent)" opacity=".55" />
          <path
            d="M78 100C90 78 118 78 124 98S104 128 86 118"
            fill="none"
            stroke="var(--accent)"
            strokeWidth="2.4"
            strokeLinecap="round"
            opacity=".5"
          />
        </g>
      </>
    );
  }
  return (
    <>
      <circle className="pool" cx="100" cy="100" r="57" fill="var(--accent-text)" opacity=".34" />
      <g className="pop">
        <circle
          cx="100"
          cy="100"
          r="44"
          fill="none"
          stroke="var(--text)"
          strokeWidth="1.5"
          opacity=".45"
        />
        <circle
          cx="100"
          cy="100"
          r="28"
          fill="none"
          stroke="var(--text)"
          strokeWidth="1.5"
          opacity=".4"
        />
        <ellipse
          cx="82"
          cy="80"
          rx="14"
          ry="6"
          fill="var(--text)"
          opacity=".22"
          transform="rotate(-30 82 80)"
        />
      </g>
    </>
  );
}

/**
 * Рисованный «ролик» приготовления, вид сверху: чашка, кофе, струя молока, рисунок.
 * Эталон — design/preview.html (brew/artOf). Играет, только когда виден.
 */
export function BrewView({
  variant = "heart",
  milkColor = "var(--liquid-milk)",
  durationSec = 9,
  paused = false,
  title = "Как готовится напиток",
  className = "",
}: Props) {
  const uid = useId().replace(/[^a-zA-Z0-9]/g, "");
  const [ref, visible] = useVisible<HTMLDivElement>();
  const reduced = useReducedMotion();
  const hold = paused || !visible || reduced;

  return (
    <div ref={ref} className={className}>
      <svg
        className={`brew${hold ? " brew-paused" : ""}`}
        viewBox="0 0 200 200"
        role="img"
        aria-label={title}
        style={{ "--m": milkColor, "--dur": `${durationSec}s` } as React.CSSProperties}
      >
        <defs>
          <radialGradient id={`cer-${uid}`} cx="35%" cy="30%" r="80%">
            <stop offset="0" stopColor="var(--liquid-coconut)" />
            <stop offset=".7" stopColor="var(--liquid-almond)" />
            <stop offset="1" stopColor="var(--text-2)" />
          </radialGradient>
          <radialGradient id={`cof-${uid}`} cx="50%" cy="45%" r="62%">
            <stop offset="0" stopColor="var(--liquid-coffee)" />
            <stop offset=".6" stopColor="var(--liquid-coffee-strong)" />
            <stop offset="1" stopColor="var(--bg)" />
          </radialGradient>
          <radialGradient id={`crema-${uid}`} cx="50%" cy="50%" r="50%">
            <stop offset="0" stopColor="var(--accent-text)" stopOpacity=".9" />
            <stop offset="1" stopColor="var(--accent-text)" stopOpacity="0" />
          </radialGradient>
        </defs>
        <circle cx="100" cy="100" r="96" fill={`url(#cer-${uid})`} />
        <circle cx="100" cy="100" r="80" fill="none" stroke="var(--text-3)" strokeWidth="1.5" />
        <path d="M160 90h24a10 10 0 0 1 0 20h-24z" fill={`url(#cer-${uid})`} />
        <circle cx="100" cy="100" r="70" fill={`url(#cer-${uid})`} />
        <circle cx="100" cy="100" r="62" fill="var(--liquid-almond)" />
        <circle cx="100" cy="100" r="58" fill={`url(#cof-${uid})`} />
        <g className="spin">
          <ellipse cx="100" cy="100" rx="50" ry="24" fill={`url(#crema-${uid})`} opacity=".55" />
        </g>
        <circle
          className="rip"
          cx="100"
          cy="100"
          r="40"
          fill="none"
          stroke="var(--accent-text)"
          strokeWidth="1.6"
        />
        <Art variant={variant} />
        <path className="stream" d="M96 -2H104L101.5 98H98.5Z" fill="var(--m)" />
      </svg>
    </div>
  );
}
