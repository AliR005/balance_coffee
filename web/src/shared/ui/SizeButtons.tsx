export interface SizeOption {
  value: string;
  label: string;
  hint?: string;
}

interface Props {
  options: SizeOption[];
  value: string;
  onChange: (value: string) => void;
  label: string;
}

/** Три крупные кнопки объёма (пилюли-тайлы). */
export function SizeButtons({ options, value, onChange, label }: Props) {
  return (
    <div role="group" aria-label={label} className="grid grid-cols-3 gap-2.5">
      {options.map((o) => {
        const active = o.value === value;
        return (
          <button
            key={o.value}
            type="button"
            aria-pressed={active}
            onClick={() => onChange(o.value)}
            className={`flex h-14 flex-col items-center justify-center rounded-tile border leading-tight font-semibold transition-colors duration-200 ${
              active
                ? "border-[var(--primary)] bg-[var(--primary)] text-on-primary"
                : "border-[var(--line-strong)] text-text"
            }`}
          >
            {o.label}
            {o.hint ? (
              <small className={`text-[11px] font-normal ${active ? "opacity-70" : "text-text-2"}`}>
                {o.hint}
              </small>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
