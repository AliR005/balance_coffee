interface Props {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
}

/** Переключатель с role="switch". */
export function Switch({ checked, onChange, label }: Props) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={`relative h-7 w-[46px] shrink-0 rounded-[14px] transition-colors duration-200 ${
        checked ? "bg-[var(--panel-solid)]" : "bg-[var(--surface-3)]"
      }`}
    >
      <span
        aria-hidden
        className="absolute top-[3px] left-[3px] block h-[22px] w-[22px] rounded-full bg-[var(--primary)] shadow transition-transform duration-300"
        style={{ transform: checked ? "translateX(18px)" : "none" }}
      />
    </button>
  );
}
