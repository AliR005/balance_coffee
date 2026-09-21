import { useNavigate } from "react-router-dom";
import { Button } from "../../shared/ui/Button";
import { Glass } from "../../shared/ui/Glass";
import { Splash } from "../../shared/ui/Splash";
import { useT } from "../../shared/i18n";
import { markWelcomeSeen } from "../cart/store";

/** Стартовый экран: один раз при первом запуске. */
export function StartPage() {
  const t = useT();
  const nav = useNavigate();

  const go = (path: string) => {
    markWelcomeSeen();
    nav(path);
  };

  return (
    <main className="relative mx-auto flex min-h-dvh w-full max-w-[480px] flex-col overflow-hidden bg-[radial-gradient(70%_45%_at_50%_40%,var(--glow),transparent_70%),linear-gradient(var(--surface),var(--bg))]">
      <div className="pt-14">
        <Splash label={t.brand} />
      </div>
      <Glass animated className="mx-auto mt-6 w-[300px] drop-shadow-[0_30px_40px_rgb(0_0_0/.55)]" />
      <div className="px-6 text-center">
        <span className="font-script block -rotate-3 text-4xl leading-none text-primary">
          {t.tagline}
        </span>
        <h3 className="mt-2.5 text-[28px] leading-tight font-light tracking-tight">
          {t.heroTitle}
        </h3>
      </div>
      <div className="mt-auto flex gap-2.5 p-5 pb-[calc(var(--space-5)+var(--safe-bottom))]">
        <div className="flex-1 [&>button]:w-full">
          <Button onClick={() => go("/menu")}>{t.orderNow}</Button>
        </div>
        <Button variant="ghost" onClick={() => go("/menu")}>
          {t.lookMenu}
        </Button>
      </div>
    </main>
  );
}
