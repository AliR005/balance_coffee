export interface TabItem {
  id: string;
  label: string;
  icon: React.ReactNode;
}

interface Props {
  tabs: TabItem[];
  active: string;
  onChange: (id: string) => void;
}

/** Плавающая пилюля навигации; активный пункт персиковый. */
export function TabBar({ tabs, active, onChange }: Props) {
  return (
    <nav
      aria-label="Разделы"
      className="fixed inset-x-3 bottom-[calc(var(--space-4)+var(--safe-bottom))] z-40 flex h-16 items-center justify-around rounded-control border border-[var(--line)] bg-[var(--glass-bg)] backdrop-blur-[var(--glass-blur)]"
    >
      {tabs.map((t) => {
        const on = t.id === active;
        return (
          <button
            key={t.id}
            type="button"
            onClick={() => onChange(t.id)}
            aria-current={on ? "page" : undefined}
            className={`flex min-w-16 flex-col items-center gap-0.5 text-[10px] ${on ? "text-primary" : "text-text-2"}`}
          >
            {t.icon}
            {t.label}
          </button>
        );
      })}
    </nav>
  );
}
