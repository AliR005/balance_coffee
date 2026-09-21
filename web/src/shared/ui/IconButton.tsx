import type { ButtonHTMLAttributes } from "react";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  glass?: boolean;
  label: string;
}

/** Круглая иконка-кнопка 44px; glass — поверх видео. */
export function IconButton({ glass = false, label, children, className = "", ...rest }: Props) {
  const glassCls = glass
    ? "bg-[var(--glass-bg)] backdrop-blur-[var(--glass-blur)] border border-[var(--line)]"
    : "border border-[var(--line-strong)]";
  return (
    <button
      type="button"
      aria-label={label}
      className={`grid h-11 w-11 place-items-center rounded-full ${glassCls} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}
