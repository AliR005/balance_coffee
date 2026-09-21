/** Скелетон-заглушка загрузки. */
export function Skeleton({
  className = "",
  label = "Загружаем",
}: {
  className?: string;
  label?: string;
}) {
  return (
    <div
      role="status"
      aria-label={label}
      className={`animate-pulse rounded-tile bg-surface-2 ${className}`}
    >
      <span className="sr-only">{label}</span>
    </div>
  );
}
