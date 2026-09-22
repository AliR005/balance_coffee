import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import type { LocationOut, OrderOut } from "../../shared/api/generated/api";
import { getGetOrderOrdersOrderIdGetUrl } from "../../shared/api/generated/api";
import { apiGet } from "../../shared/api/base";
import { useT } from "../../shared/i18n";
import { Button } from "../../shared/ui/Button";
import { Chip } from "../../shared/ui/Chip";
import { LiveCard } from "../../shared/ui/LiveCard";
import { Logo } from "../../shared/ui/Logo";
import { Sheet } from "../../shared/ui/Sheet";
import { Skeleton } from "../../shared/ui/Skeleton";
import { TabBar } from "../../shared/ui/TabBar";
import { Toast } from "../../shared/ui/Toast";
import { useCart } from "../cart/store";
import { myOrders } from "../orders/registry";
import { rebuildOrder } from "../orders/repeat";
import { useLocations, useMenu } from "./api";
import { brewVariantOf } from "./brew";

function useTabs() {
  const nav = useNavigate();
  const t = useT();
  return {
    tabs: [
      { id: "menu", label: t.tabs.menu, icon: <span aria-hidden>☕</span> },
      { id: "orders", label: t.tabs.orders, icon: <span aria-hidden>🧾</span> },
      { id: "bonus", label: t.tabs.bonus, icon: <span aria-hidden>★</span> },
      { id: "profile", label: t.tabs.profile, icon: <span aria-hidden>☺</span> },
    ],
    onChange: (id: string) => {
      if (id === "menu") nav("/menu");
      else if (id === "orders") nav("/orders");
      else if (id === "bonus") nav("/bonus");
      else nav("/profile");
    },
  };
}

/** Кремовая карточка «Повторить последний заказ» — если есть прошлый заказ. */
function RepeatCard({ onRepeat }: { onRepeat: (msg: string) => void }) {
  const t = useT();
  const nav = useNavigate();
  const locationId = useCart((s) => s.locationId);
  const setLocation = useCart((s) => s.setLocation);
  const addItem = useCart((s) => s.addItem);
  const [last] = useState(() => myOrders()[0] ?? null);

  const menuQuery = useMenu(last?.locationId ?? locationId);
  const orderQuery = useQuery({
    queryKey: ["order", last?.id],
    queryFn: (): Promise<OrderOut> =>
      apiGet<OrderOut>(
        `${getGetOrderOrdersOrderIdGetUrl(last?.id ?? 0)}?token=${encodeURIComponent(last?.token ?? "")}`,
      ),
    enabled: last !== null,
    staleTime: 60_000,
  });

  if (!last || !orderQuery.data) return null;
  const firstName = orderQuery.data.items?.[0]?.product_name ?? "";
  return (
    <div className="mx-5 mt-3.5 flex items-center gap-3 rounded-tile border border-[var(--line)] bg-surface p-2.5 pl-3.5">
      <span className="flex-1 text-[13px]">
        <b className="block text-sm">
          {firstName}, {orderQuery.data.code}
        </b>
        <span className="text-text-2">{t.repeatLast}</span>
      </span>
      <Button
        onClick={() => {
          if (!menuQuery.data) return;
          const { ok, dropped } = rebuildOrder(menuQuery.data, orderQuery.data?.items ?? []);
          if (ok.length === 0) {
            onRepeat(t.repeatDropped);
            return;
          }
          setLocation(last.locationId, { clear: true });
          ok.forEach((it) => addItem(last.locationId, it));
          onRepeat(dropped.length > 0 ? t.repeatDropped : t.added);
          nav("/checkout");
        }}
      >
        {t.repeat}
      </Button>
    </div>
  );
}

export function MenuPage() {
  const t = useT();
  const nav = useNavigate();
  const { tabs, onChange } = useTabs();
  const locationId = useCart((s) => s.locationId);
  const setLocation = useCart((s) => s.setLocation);
  const cartCount = useCart((s) => s.count());
  const hasItems = useCart((s) => s.items.length > 0);

  const locQuery = useLocations();
  const [locSheet, setLocSheet] = useState(false);
  const [pendingLoc, setPendingLoc] = useState<LocationOut | null>(null);
  const [category, setCategory] = useState<string>("all");
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(timer);
  }, [toast]);

  // Первая точка по умолчанию.
  useEffect(() => {
    if (locationId === null && locQuery.data && locQuery.data.length > 0) {
      const first = locQuery.data[0];
      if (first) setLocation(first.id);
    }
  }, [locationId, locQuery.data, setLocation]);

  const menuQuery = useMenu(locationId);
  const currentLoc = locQuery.data?.find((l) => l.id === locationId) ?? null;

  const pickLocation = (loc: LocationOut) => {
    if (loc.id === locationId) {
      setLocSheet(false);
      return;
    }
    if (hasItems) {
      setPendingLoc(loc);
    } else {
      setLocation(loc.id);
      setLocSheet(false);
    }
  };

  const categories = menuQuery.data?.categories ?? [];
  const visibleCats =
    category === "all" ? categories : categories.filter((c) => c.slug === category);

  return (
    <main className="mx-auto min-h-dvh w-full max-w-[480px] bg-bg pb-28 text-text">
      <div className="flex items-center justify-between px-5 pt-4">
        <span className="flex items-center gap-2 text-[19px] font-semibold">
          <Logo size={28} />
          {t.brand}
        </span>
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => setLocSheet(true)}
            className="inline-flex h-9 items-center gap-1.5 rounded-control border border-[var(--line)] bg-surface-2 px-3 text-[13px] font-medium"
            aria-label={t.chooseLocation}
          >
            <span aria-hidden className="text-accent-text">
              ◆
            </span>
            {currentLoc ? currentLoc.name : "…"}
            <span aria-hidden>›</span>
          </button>
          <button
            type="button"
            onClick={() => nav("/checkout")}
            aria-label={t.cart}
            className="relative grid h-11 w-11 place-items-center"
          >
            <span aria-hidden className="text-xl">
              🧺
            </span>
            {cartCount > 0 ? (
              <span
                key={cartCount}
                className="tabular absolute top-1 right-0.5 grid h-[18px] min-w-[18px] animate-bounce place-items-center rounded-full bg-[var(--primary)] px-1 text-[11px] font-bold text-on-primary"
              >
                {cartCount}
              </span>
            ) : null}
          </button>
        </div>
      </div>

      <h1 className="px-5 pt-4 text-[30px] leading-tight font-normal tracking-tight">
        {t.menuTitle}
      </h1>
      <p className="max-w-[320px] px-5 pt-2 text-sm text-text-2">{t.menuSubtitle}</p>

      <RepeatCard onRepeat={(msg) => setToast(msg)} />

      {menuQuery.isLoading || locQuery.isLoading ? (
        <div className="grid grid-cols-2 gap-3 p-5" role="status" aria-label={t.loading}>
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="aspect-[3/4]" />
          ))}
        </div>
      ) : menuQuery.isError || locQuery.isError ? (
        <div className="flex flex-col items-center gap-3 p-10 text-center">
          <p className="text-sm text-text-2">{t.error}</p>
          <Button
            variant="ghost"
            onClick={() => {
              void locQuery.refetch();
              void menuQuery.refetch();
            }}
          >
            {t.retry}
          </Button>
        </div>
      ) : (
        <>
          <div
            className="sticky top-0 z-10 flex gap-2 overflow-x-auto bg-bg px-5 py-3.5"
            role="group"
            aria-label="Категории"
          >
            <Chip pressed={category === "all"} onClick={() => setCategory("all")}>
              {t.all}
            </Chip>
            {categories.map((c) => (
              <Chip key={c.slug} pressed={category === c.slug} onClick={() => setCategory(c.slug)}>
                {c.name}
              </Chip>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-3 px-5">
            {visibleCats
              .flatMap((c) => c.products ?? [])
              .map((p) => (
                <LiveCard
                  key={p.id}
                  name={p.name}
                  description={p.description ?? ""}
                  priceKopeks={p.base_price}
                  available={p.available ?? true}
                  variant={brewVariantOf(p)}
                  durationSec={p.video_duration_sec ?? 9}
                  onAdd={(p.available ?? true) ? () => nav(`/drink/${p.id}`) : undefined}
                />
              ))}
            {visibleCats.every((c) => (c.products ?? []).length === 0) ? (
              <p className="col-span-2 px-3 py-10 text-center text-sm text-text-2">
                {t.emptyCategory}
              </p>
            ) : null}
          </div>
        </>
      )}

      <Sheet
        open={locSheet}
        onClose={() => {
          setLocSheet(false);
          setPendingLoc(null);
        }}
        label={t.chooseLocation}
      >
        {pendingLoc ? (
          <div className="flex flex-col gap-3">
            <h3 className="text-lg font-medium">{t.locationConfirmTitle}</h3>
            <p className="text-sm text-text-2">{t.locationConfirmText}</p>
            <div className="flex gap-2.5">
              <Button variant="ghost" onClick={() => setPendingLoc(null)}>
                {t.keep}
              </Button>
              <Button
                onClick={() => {
                  setLocation(pendingLoc.id, { clear: true });
                  setPendingLoc(null);
                  setLocSheet(false);
                }}
              >
                {t.change}
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            <h3 className="mb-1 text-lg font-medium">{t.chooseLocation}</h3>
            {locQuery.data?.map((l) => (
              <button
                key={l.id}
                type="button"
                onClick={() => pickLocation(l)}
                aria-pressed={l.id === locationId}
                className={`flex items-center gap-2.5 rounded-tile border p-3.5 text-left ${
                  l.id === locationId
                    ? "border-[var(--primary)] bg-surface-2"
                    : "border-[var(--line)]"
                }`}
              >
                <span className="flex-1">
                  <b className="block text-[15px] font-semibold">{l.name}</b>
                  <small className="block text-xs text-text-2">
                    {l.address} · {l.is_open_now ? t.openNow : t.closed}
                  </small>
                </span>
                {l.id === locationId ? (
                  <span aria-hidden className="text-primary">
                    ●
                  </span>
                ) : null}
              </button>
            ))}
          </div>
        )}
      </Sheet>

      <Toast message={toast} />
      <TabBar tabs={tabs} active="menu" onChange={onChange} />
    </main>
  );
}
