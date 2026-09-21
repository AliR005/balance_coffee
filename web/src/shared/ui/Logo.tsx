/** Логотип-заглушка из design/assets/logo-b.svg (currentColor). Заменить официальным. */
export function Logo({ size = 28, label = "balance" }: { size?: number; label?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      role="img"
      aria-label={label}
      className="text-primary"
    >
      <rect x="14" y="6" width="22" height="88" rx="11" fill="currentColor" />
      <circle cx="60" cy="66" r="24" stroke="currentColor" strokeWidth="18" />
    </svg>
  );
}
