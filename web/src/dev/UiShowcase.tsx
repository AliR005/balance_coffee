import { useState } from "react";
import { BonusRing } from "../shared/ui/BonusRing";
import { BrewView, type BrewVariant } from "../shared/ui/BrewView";
import { Button } from "../shared/ui/Button";
import { Chip } from "../shared/ui/Chip";
import { DrinkPlayer } from "../shared/ui/DrinkPlayer";
import { Glass } from "../shared/ui/Glass";
import { IconButton } from "../shared/ui/IconButton";
import { LiveCard } from "../shared/ui/LiveCard";
import { Logo } from "../shared/ui/Logo";
import { PriceText } from "../shared/ui/PriceText";
import { Sheet } from "../shared/ui/Sheet";
import { SizeButtons } from "../shared/ui/SizeButtons";
import { Skeleton } from "../shared/ui/Skeleton";
import { Splash } from "../shared/ui/Splash";
import { Stepper } from "../shared/ui/Stepper";
import { Switch } from "../shared/ui/Switch";
import { TabBar } from "../shared/ui/TabBar";
import { Toast } from "../shared/ui/Toast";

const VARIANTS: BrewVariant[] = ["heart", "tulip", "full", "crema"];
const MILKS = [
  "var(--liquid-milk)",
  "var(--liquid-oat)",
  "var(--liquid-almond)",
  "var(--liquid-coconut)",
];

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-panel border border-[var(--line)] bg-surface p-6">
      <h3 className="mb-3.5 text-lg font-medium">{title}</h3>
      <div className="flex flex-wrap items-center gap-3">{children}</div>
    </section>
  );
}

/** Витрина дизайн-системы — только dev-сборка. */
export function UiShowcase() {
  const [count, setCount] = useState(1);
  const [size, setSize] = useState("M");
  const [chip, setChip] = useState("classic");
  const [sw, setSw] = useState(false);
  const [sheet, setSheet] = useState(false);
  const [tab, setTab] = useState("menu");
  const [variant, setVariant] = useState<BrewVariant>("heart");
  const [milk, setMilk] = useState(MILKS[0] ?? "var(--liquid-milk)");

  return (
    <main className="mx-auto grid max-w-3xl gap-5 bg-bg p-5 pb-28 text-text">
      <h2 className="text-2xl font-normal">Дизайн-система</h2>

      <Section title="Кнопки">
        <Button>Заказать</Button>
        <Button loading>Заказать</Button>
        <Button variant="ghost">Меню</Button>
        <IconButton label="Назад">←</IconButton>
        <IconButton glass label="Пауза">
          ⏸
        </IconButton>
      </Section>

      <Section title="Чипы и размеры">
        {["classic", "author", "cold"].map((c) => (
          <Chip key={c} pressed={chip === c} onClick={() => setChip(c)}>
            {c}
          </Chip>
        ))}
        <div className="w-full">
          <SizeButtons
            label="Объём"
            value={size}
            onChange={setSize}
            options={[
              { value: "S", label: "S", hint: "200 мл" },
              { value: "M", label: "M", hint: "300 мл" },
              { value: "L", label: "L", hint: "400 мл" },
            ]}
          />
        </div>
      </Section>

      <Section title="Степпер, переключатель, цена">
        <Stepper label="Количество" value={count} onChange={setCount} />
        <Switch label="Списать баллы" checked={sw} onChange={setSw} />
        <PriceText kopeks={32000} className="text-2xl" />
      </Section>

      <Section title="BrewView — варианты и молоко">
        <div className="flex w-full flex-wrap gap-2">
          {VARIANTS.map((v) => (
            <Chip key={v} pressed={variant === v} onClick={() => setVariant(v)}>
              {v}
            </Chip>
          ))}
        </div>
        <div className="flex w-full flex-wrap gap-2">
          {MILKS.map((m) => (
            <Chip key={m} pressed={milk === m} onClick={() => setMilk(m)}>
              {m.replace("var(--liquid-", "").replace(")", "")}
            </Chip>
          ))}
        </div>
        <BrewView variant={variant} milkColor={milk} durationSec={9} className="w-52" />
      </Section>

      <Section title="LiveCard">
        <div className="grid w-full grid-cols-2 gap-3">
          <LiveCard
            name="Латте"
            description="Нежный, бархатный"
            priceKopeks={32000}
            onAdd={() => {}}
          />
          <LiveCard
            name="Колд брю"
            description="Бодрит мягко"
            priceKopeks={34000}
            available={false}
          />
        </div>
      </Section>

      <Section title="DrinkPlayer">
        <div className="w-full">
          <DrinkPlayer
            steps={[
              { title: "Эспрессо", atSec: 0 },
              { title: "Молоко", atSec: 3 },
              { title: "Рисунок", atSec: 6 },
            ]}
            durationSec={9}
            variant="heart"
          />
        </div>
      </Section>

      <Section title="BonusRing">
        <BonusRing balance={320} progress={0.68} />
      </Section>

      <Section title="Glass и Splash">
        <Glass className="w-40" />
        <Splash />
        <Logo />
      </Section>

      <Section title="Sheet, Skeleton, Toast">
        <Button variant="ghost" onClick={() => setSheet(true)}>
          Открыть sheet
        </Button>
        <Skeleton className="h-14 w-40" />
        <Toast message="Нет связи. Пробуем снова." actionLabel="Повторить" />
      </Section>

      <Sheet open={sheet} onClose={() => setSheet(false)} label="Пример">
        <p>Sheet с фокус-ловушкой и drag-to-close.</p>
        <Button onClick={() => setSheet(false)}>Закрыть</Button>
      </Sheet>

      <TabBar
        active={tab}
        onChange={setTab}
        tabs={[
          { id: "home", label: "Главная", icon: <span aria-hidden>⌂</span> },
          { id: "menu", label: "Меню", icon: <span aria-hidden>☕</span> },
          { id: "bonus", label: "Бонусы", icon: <span aria-hidden>★</span> },
          { id: "profile", label: "Профиль", icon: <span aria-hidden>☺</span> },
        ]}
      />
    </main>
  );
}
