import { formatDuration } from "../lib/format";
import { BrewView, type BrewVariant } from "./BrewView";
import { PriceText } from "./PriceText";

interface Props {
  name: string;
  description: string;
  priceKopeks: number;
  available?: boolean;
  variant?: BrewVariant;
  milkColor?: string;
  durationSec?: number;
  onAdd?: () => void;
}

/** Живая карточка напитка 3:4: ролик на весь фон, бейдж длительности, цена, круглая «+». */
export function LiveCard({
  name,
  description,
  priceKopeks,
  available = true,
  variant,
  milkColor,
  durationSec = 9,
  onAdd,
}: Props) {
  return (
    <article
      aria-label={name}
      style={{ "--dur": `${durationSec}s` } as React.CSSProperties}
      className={`relative aspect-[3/4] overflow-hidden rounded-card border border-[var(--line)] bg-surface ${
        available ? "" : "opacity-70"
      }`}
    >
      <div className="absolute inset-0 grid place-items-start justify-center bg-[radial-gradient(75%_55%_at_50%_34%,var(--glow),transparent_72%),linear-gradient(var(--surface-2),var(--bg))] pt-3.5">
        <BrewView
          variant={variant}
          milkColor={milkColor}
          durationSec={durationSec}
          className="w-[76%] drop-shadow-[0_12px_16px_rgb(0_0_0/.6)]"
        />
      </div>
      <div className="absolute inset-x-0 bottom-0 h-[58%] bg-[linear-gradient(transparent,rgb(10_8_7/.94)_66%)]" />
      <span className="absolute top-2.5 right-2.5 inline-flex h-6 items-center gap-1 rounded-xl border border-[var(--line)] bg-[var(--glass-bg)] px-2 text-[11px] font-medium backdrop-blur">
        <span aria-hidden>▶</span>
        <span className="tabular">{formatDuration(durationSec)}</span>
      </span>
      <div className="absolute right-3 bottom-3 left-3">
        <h4 className="text-base font-semibold">{name}</h4>
        <p className="mt-0.5 mb-2 line-clamp-2 text-[11px] leading-[1.3] text-text-2">
          {description}
        </p>
        <div className="flex items-center justify-between">
          {available ? (
            <PriceText kopeks={priceKopeks} className="text-base" />
          ) : (
            <span className="text-base text-text-2">Закончилось</span>
          )}
          {available && onAdd ? (
            <button
              type="button"
              onClick={onAdd}
              aria-label={`Добавить: ${name}`}
              className="grid h-[34px] w-[34px] place-items-center rounded-full bg-[var(--primary)] text-xl leading-none text-on-primary transition-transform active:scale-[.88]"
            >
              +
            </button>
          ) : null}
        </div>
      </div>
      <i
        aria-hidden
        className="brew-progress absolute inset-x-0 bottom-0 h-[2px] bg-[var(--primary)] opacity-90"
      />
    </article>
  );
}
