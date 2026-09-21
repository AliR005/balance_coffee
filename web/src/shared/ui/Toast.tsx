interface Props {
  message: string | null;
  actionLabel?: string;
  onAction?: () => void;
}

/** Тост-ошибка/инфо с действием. */
export function Toast({ message, actionLabel, onAction }: Props) {
  if (!message) return null;
  return (
    <div
      role="status"
      className="fixed inset-x-5 bottom-[calc(var(--space-5)+var(--safe-bottom))] z-50 flex items-center gap-3 rounded-tile bg-surface-3 px-4 py-3 text-sm shadow-[var(--shadow-float)]"
    >
      <span className="flex-1">{message}</span>
      {actionLabel ? (
        <button type="button" onClick={onAction} className="font-semibold text-primary">
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}
