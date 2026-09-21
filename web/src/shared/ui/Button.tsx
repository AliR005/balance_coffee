import { motion } from "framer-motion";
import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "ghost";

interface Props extends Omit<
  ButtonHTMLAttributes<HTMLButtonElement>,
  "onDrag" | "onDragStart" | "onDragEnd" | "onAnimationStart" | "onAnimationComplete"
> {
  variant?: Variant;
  loading?: boolean;
}

/** Главная кнопка — одна на экране: персиковый градиент. Loading без скачка ширины. */
export function Button({
  variant = "primary",
  loading = false,
  disabled,
  children,
  ...rest
}: Props) {
  const cls =
    variant === "primary"
      ? "bg-[linear-gradient(180deg,var(--primary),var(--primary-2))] text-on-primary shadow-[var(--shadow-cta)]"
      : "border border-[var(--line-strong)] text-text";
  return (
    <motion.button
      whileTap={{ scale: 0.97 }}
      transition={{ duration: 0.15 }}
      disabled={disabled ?? loading}
      aria-busy={loading}
      className={`inline-flex h-12 items-center justify-center gap-2.5 rounded-control px-6 text-[15px] font-semibold whitespace-nowrap disabled:opacity-60 ${cls}`}
      {...rest}
    >
      {loading ? (
        <span
          aria-hidden
          className="inline-block h-5 w-5 animate-spin rounded-full border-2 border-current border-t-transparent"
        />
      ) : null}
      {children}
    </motion.button>
  );
}
