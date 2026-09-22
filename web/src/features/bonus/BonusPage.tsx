import { useNavigate } from "react-router-dom";
import { useT } from "../../shared/i18n";
import { formatRub } from "../../shared/lib/format";
import { BonusRing } from "../../shared/ui/BonusRing";
import { Button } from "../../shared/ui/Button";
import { Skeleton } from "../../shared/ui/Skeleton";
import { TabBar } from "../../shared/ui/TabBar";
import { useBonusAccount, useBonusTransactions } from "./api";
import { levelProgress } from "./math";

/** Экран «Бонусы»: кольцо, уровень, как зарабатывать, история. */
export function BonusPage() {
  const t = useT();
  const nav = useNavigate();
  const accountQuery = useBonusAccount();
  const txnsQuery = useBonusTransactions();

  const goTab = (id: string) => {
    if (id === "menu") nav("/menu");
    else if (id === "orders") nav("/orders");
    else if (id === "profile") nav("/profile");
  };

  if (accountQuery.isLoading) {
    return (
      <main className="mx-auto w-full max-w-[480px] bg-bg p-5" role="status" aria-label={t.loading}>
        <Skeleton className="mx-auto h-[210px] w-[210px] rounded-full" />
        <Skeleton className="mt-5 h-24" />
      </main>
    );
  }

  if (!accountQuery.data) {
    return (
      <main className="mx-auto flex min-h-dvh w-full max-w-[480px] flex-col items-center justify-center gap-3 bg-bg p-10 text-center">
        <h2 className="text-2xl font-normal">{t.tabs.bonus}</h2>
        <p className="text-sm text-text-2">{t.bonusEmpty}</p>
        <Button onClick={() => nav("/menu")}>{t.lookMenu}</Button>
        <TabBar
          active="bonus"
          onChange={goTab}
          tabs={[
            { id: "menu", label: t.tabs.menu, icon: <span aria-hidden>☕</span> },
            { id: "orders", label: t.tabs.orders, icon: <span aria-hidden>🧾</span> },
            { id: "bonus", label: t.tabs.bonus, icon: <span aria-hidden>★</span> },
            { id: "profile", label: t.tabs.profile, icon: <span aria-hidden>☺</span> },
          ]}
        />
      </main>
    );
  }

  const acc = accountQuery.data;
  const lifetime = acc.lifetime_spent ?? 0;
  const toNext = acc.level.to_next_kopeks ?? 0;
  const hasNext = acc.level.next_name !== null && acc.level.next_name !== undefined;
  const progress = levelProgress(lifetime, toNext, hasNext);
  const txns = txnsQuery.data ?? [];

  return (
    <main className="mx-auto min-h-dvh w-full max-w-[480px] bg-bg pb-28 text-text">
      <h1 className="pt-4 text-center text-lg font-medium">{t.tabs.bonus}</h1>

      <div className="mt-3.5">
        <BonusRing balance={acc.balance} progress={progress} />
      </div>

      <section className="mx-5 mt-5 rounded-tile border border-[var(--line)] bg-surface p-4">
        <div className="flex justify-between text-[13px] text-text-2">
          <span>
            {t.level}: <b className="text-text">«{acc.level.name}»</b>
          </span>
          {acc.level.next_name ? (
            <span>
              {t.toNext}: <b className="tabular text-text">{formatRub(toNext)}</b>
            </span>
          ) : null}
        </div>
        <div
          className="my-3 h-1.5 overflow-hidden rounded bg-surface-3"
          role="progressbar"
          aria-valuenow={Math.round(progress * 100)}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className="h-full rounded bg-[var(--primary)] transition-transform duration-1000"
            style={{ transform: `scaleX(${progress})`, transformOrigin: "left" }}
          />
        </div>
        <div className="flex justify-between text-xs text-text-3">
          <span>Эспрессо</span>
          <span>Латте</span>
          <span>Баланс</span>
        </div>
      </section>

      <section className="mx-5 mt-5">
        <h2 className="mb-2.5 text-[15px] font-medium">{t.howEarn}</h2>
        {[
          ["☕", t.earnCoffee, t.earnCoffeeHint],
          ["★", t.earnGift, t.earnGiftHint],
        ].map(([icon, title, hint]) => (
          <div
            key={title}
            className="flex items-center gap-3 border-t border-[var(--line)] py-3 text-sm"
          >
            <span aria-hidden className="text-accent-text">
              {icon}
            </span>
            <span className="flex-1">{title}</span>
            <em className="text-[13px] text-text-2 not-italic">{hint}</em>
          </div>
        ))}
      </section>

      <section className="mx-5 mt-5">
        <h2 className="mb-1.5 text-[15px] font-medium">{t.history}</h2>
        {txns.map((txn) => (
          <div
            key={txn.id}
            className="flex justify-between border-t border-[var(--line)] py-2.5 text-sm"
          >
            <span>
              {txn.type === "accrual"
                ? t.txnAccrual
                : txn.type === "redeem"
                  ? t.txnRedeem
                  : t.txnAdjust}
              <small className="block text-xs text-text-2">
                {new Date(txn.created_at).toLocaleDateString("ru-RU")}
              </small>
            </span>
            <em
              className={`font-semibold not-italic ${txn.amount >= 0 ? "text-success" : "text-text-2"}`}
            >
              {txn.amount >= 0 ? `+${txn.amount}` : `${txn.amount}`}
            </em>
          </div>
        ))}
      </section>

      <div className="fixed inset-x-0 bottom-24 z-30 mx-auto w-full max-w-[480px] px-5">
        <div className="[&>button]:w-full">
          <Button onClick={() => nav("/checkout")}>{t.spendBonus}</Button>
        </div>
      </div>

      <TabBar
        active="bonus"
        onChange={goTab}
        tabs={[
          { id: "menu", label: t.tabs.menu, icon: <span aria-hidden>☕</span> },
          { id: "orders", label: t.tabs.orders, icon: <span aria-hidden>🧾</span> },
          { id: "bonus", label: t.tabs.bonus, icon: <span aria-hidden>★</span> },
          { id: "profile", label: t.tabs.profile, icon: <span aria-hidden>☺</span> },
        ]}
      />
    </main>
  );
}
