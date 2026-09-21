import { Logo } from "./Logo";

const DROPS: Array<[size: number, top: number, dx: number, dy: number, delay: number]> = [
  [8, 0, 30, -26, 1],
  [14, 4, 46, -6, 1.08],
  [6, 8, 36, 18, 1.16],
  [10, -2, 20, -38, 1.24],
  [7, 10, 52, 10, 1.32],
  [9, 6, 60, -20, 1.4],
];

/** Брызги молока из логотипа — один раз на старте. */
export function Splash({ label = "balance" }: { label?: string }) {
  return (
    <div className="relative flex justify-center text-primary">
      <Logo size={56} label={label} />
      <div aria-hidden className="absolute top-[26px] left-1/2">
        {DROPS.map(([size, top, dx, dy, delay], i) => (
          <i
            key={i}
            className="splash-drop absolute"
            style={
              {
                width: size,
                height: size,
                left: 8 + i * 2,
                top,
                "--dx": `${dx}px`,
                "--dy": `${dy}px`,
                animationDelay: `${delay}s`,
              } as React.CSSProperties
            }
          />
        ))}
      </div>
    </div>
  );
}
