import { useEffect, useState } from "react";
import { formatDuration } from "../lib/format";
import { activeStepIndex, type VideoStep } from "../lib/steps";
import { BrewVideo } from "./BrewVideo";
import type { BrewVariant } from "./BrewView";
import { IconButton } from "./IconButton";

interface Props {
  steps: VideoStep[];
  durationSec?: number;
  variant?: BrewVariant;
  milkColor?: string;
  videoUrl?: string;
  posterUrl?: string;
  title?: string;
}

/** Верх окна напитка: ролик, кнопки, пауза, прогресс, время, чипы шагов. */
export function DrinkPlayer({
  steps,
  durationSec = 9,
  variant,
  milkColor,
  videoUrl,
  posterUrl,
  title,
}: Props) {
  const [paused, setPaused] = useState(false);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (paused) return;
    const started = performance.now();
    let raf = 0;
    const tick = (now: number) => {
      setElapsed((now - started) / 1000);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [paused]);

  const active = activeStepIndex(elapsed, steps, durationSec);

  return (
    <div>
      <div
        className="relative h-[340px] overflow-hidden rounded-b-[var(--r-sheet)] bg-[radial-gradient(70%_60%_at_50%_48%,var(--glow),transparent_72%),linear-gradient(var(--surface-2),var(--bg))]"
        style={{ "--dur": `${durationSec}s` } as React.CSSProperties}
      >
        <BrewVideo
          videoUrl={videoUrl}
          posterUrl={posterUrl}
          variant={variant}
          milkColor={milkColor}
          durationSec={durationSec}
          paused={paused}
          title={title}
          className="absolute top-[66px] left-1/2 w-[212px] -translate-x-1/2 drop-shadow-[0_18px_22px_rgb(0_0_0/.6)]"
        />
        <div className="absolute inset-x-0 top-0 z-[4] flex justify-between px-5 pt-1.5">
          <IconButton glass label="Назад">
            ←
          </IconButton>
          <IconButton glass label="Звук">
            ♪
          </IconButton>
        </div>
        <div className="absolute right-4 left-4 bottom-4 z-[4] flex items-center gap-3">
          <IconButton
            glass
            label={paused ? "Воспроизвести" : "Пауза"}
            onClick={() => setPaused((p) => !p)}
            className="!h-[38px] !w-[38px]"
          >
            {paused ? "▶" : "⏸"}
          </IconButton>
          <div className="h-1 flex-1 overflow-hidden rounded bg-white/20" aria-hidden>
            <i className="brew-progress block h-full bg-[var(--primary)]" />
          </div>
          <span className="tabular text-xs text-text">
            {formatDuration(elapsed % durationSec)} / {formatDuration(durationSec)}
          </span>
        </div>
      </div>
      <div className="flex gap-2 px-5 pt-3.5" role="list" aria-label="Шаги приготовления">
        {steps.map((s, i) => (
          <span
            key={s.title}
            role="listitem"
            aria-current={i === active ? "step" : undefined}
            className={`inline-flex h-7 items-center rounded-[14px] border px-3 text-xs font-medium ${
              i === active
                ? "border-[var(--primary)] bg-[var(--primary)] text-on-primary"
                : "border-[var(--line-strong)] text-text-2"
            } ${i < 3 ? `step-live-${i + 1}` : ""}`}
            style={{ "--dur": `${durationSec}s` } as React.CSSProperties}
          >
            {i + 1} {s.title}
          </span>
        ))}
      </div>
    </div>
  );
}
