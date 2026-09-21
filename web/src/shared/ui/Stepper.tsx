interface Props {
  value: number;
  min?: number;
  max?: number;
  onChange: (value: number) => void;
  label: string;
}

/** Степпер-пилюля, область нажатия ≥ 44px. */
export function Stepper({ value, min = 1, max = 10, onChange, label }: Props) {
  return (
    <div
      role="group"
      aria-label={label}
      className="inline-flex h-11 items-center gap-0.5 rounded-control border border-[var(--line-strong)] px-1"
    >
      <button
        type="button"
        aria-label="Меньше"
        disabled={value <= min}
        onClick={() => onChange(value - 1)}
        className="grid h-9 w-9 place-items-center rounded-full text-lg disabled:opacity-40"
      >
        −
      </button>
      <output
        aria-live="polite"
        className="tabular min-w-[18px] text-center text-[13px] font-semibold"
      >
        {value}
      </output>
      <button
        type="button"
        aria-label="Больше"
        disabled={value >= max}
        onClick={() => onChange(value + 1)}
        className="grid h-9 w-9 place-items-center rounded-full text-lg disabled:opacity-40"
      >
        +
      </button>
    </div>
  );
}
