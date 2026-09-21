import type { ButtonHTMLAttributes } from "react";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  pressed: boolean;
}

/** Чип-пилюля; выбранный — персиковый. */
export function Chip({ pressed, children, ...rest }: Props) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      className={`h-9 shrink-0 rounded-control border px-4 text-[13px] font-medium whitespace-nowrap transition-colors duration-200 ${
        pressed
          ? "border-[var(--primary)] bg-[var(--primary)] text-on-primary"
          : "border-[var(--line-strong)] text-text"
      }`}
      {...rest}
    >
      {children}
    </button>
  );
}
