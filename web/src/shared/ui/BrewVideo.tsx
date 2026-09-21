import { useReducedMotion, useVisible } from "../lib/useVisible";
import { BrewView, type BrewVariant } from "./BrewView";

interface Props {
  videoUrl?: string;
  posterUrl?: string;
  variant?: BrewVariant;
  milkColor?: string;
  durationSec?: number;
  paused?: boolean;
  title?: string;
  className?: string;
}

/** Видео напитка, если есть файл; иначе рисованный BrewView. Единый интерфейс. */
export function BrewVideo({
  videoUrl,
  posterUrl,
  variant,
  milkColor,
  durationSec = 9,
  paused = false,
  title,
  className = "",
}: Props) {
  const [ref, visible] = useVisible<HTMLDivElement>();
  const reduced = useReducedMotion();

  if (!videoUrl) {
    return (
      <BrewView
        variant={variant}
        milkColor={milkColor}
        durationSec={durationSec}
        paused={paused}
        title={title}
        className={className}
      />
    );
  }

  const hold = paused || !visible || reduced;
  return (
    <div ref={ref} className={className}>
      <video
        muted
        loop
        playsInline
        autoPlay={!hold}
        poster={posterUrl}
        aria-label={title ?? "Как готовится напиток"}
        className="h-full w-full object-cover"
      >
        <source src={videoUrl} />
      </video>
    </div>
  );
}
