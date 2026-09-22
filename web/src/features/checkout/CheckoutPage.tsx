import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { MenuOut } from "../../shared/api/generated/api";
import { useT } from "../../shared/i18n";
import { formatRub } from "../../shared/lib/format";
import { Button } from "../../shared/ui/Button";
import { PriceText } from "../../shared/ui/PriceText";
import { Skeleton } from "../../shared/ui/Skeleton";
import { Stepper } from "../../shared/ui/Stepper";
import { Toast } from "../../shared/ui/Toast";
import { useCart } from "../cart/store";
import { useLocations, useMenu } from "../menu/api";
import { computePrice, selectionDeltas } from "../menu/pricing";
import { addMyOrder } from "../orders/registry";
import { newIdempotencyKey, postOrder, useSlots } from "./api";
import { isPhoneValid, useCustomerForm } from "./customer";
import type { ApiError } from "../../shared/api/base";

type Mode = "on_site" | "scheduled";

function slotLabel(iso: string, timeZone: string): string {
  return new Date(iso).toLocaleTimeString("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone,
  });
}

/** Оформление: режим, время, кто заберёт, позиции, итог. Светлая сливочная панель. */
export function CheckoutPage() {
  const t = useT();
  const nav = useNavigate();
  const locationId = useCart((s) => s.locationId);
  const items = useCart((s) => s.items);
  const setQty = useCart((s) => s.setQty);
  const removeAt = useCart((s) => s.removeAt);
  const clear = useCart((s) => s.clear);

  const menuQuery = useMenu(locationId);
  const menu: MenuOut | undefined = menuQuery.data;
  const locQuery = useLocations();
  const timeZone = locQuery.data?.find((l) => l.id === locationId)?.timezone ?? "UTC";

  const [mode, setMode] = useState<Mode>("scheduled");
  const [slot, setSlot] = useState<string>("asap");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [idempotencyKey] = useState(newIdempotencyKey);
  const customer = useCustomerForm();

  const resolved = useMemo(() => {
    if (!menu?.categories) return [];
    const all = menu.categories.flatMap((c) => c.products ?? []);
    return items.map((it, index) => {
      const prod = all.find((p) => p.id === it.productId);
      const unit = prod ? computePrice(prod.base_price, selectionDeltas(prod, it.optionIds), 1) : 0;
      return { index, item: it, name: prod?.name ?? "…", unit, line: unit * it.qty };
    });
  }, [menu, items]);

  const units = useMemo(() => {
    if (!menu?.categories) return 0;
    const prep = new Map<number, number>();
    for (const c of menu.categories ?? [])
      for (const p of c.products ?? []) prep.set(p.id, p.prep_units ?? 1);
    return items.reduce((a, it) => a + it.qty * (prep.get(it.productId) ?? 1), 0);
  }, [menu, items]);

  const slotsQuery = useSlots(locationId, units);
  const slots = slotsQuery.data;
  const asapLabel = slots?.asap ? slotLabel(slots.asap.start, timeZone) : null;

  const subtotal = resolved.reduce((a, r) => a + r.line, 0);

  if (locationId === null || items.length === 0) {
    return (
      <main className="mx-auto flex min-h-dvh w-full max-w-[480px] flex-col items-center justify-center gap-3 bg-panel p-10 text-center text-panel-text">
        <p className="text-sm text-panel-text-2">{t.cartEmpty}</p>
        <Button variant="ghost" onClick={() => nav("/menu")}>
          {t.lookMenu}
        </Button>
      </main>
    );
  }

  const submit = async () => {
    customer.setTouched(true);
    if (!customer.name.trim() || !isPhoneValid(customer.phone)) return;
    if (mode === "scheduled" && !slot) return;
    setSending(true);
    setError(null);
    try {
      const pickupAt = mode === "on_site" ? undefined : slot === "asap" ? slots?.asap?.start : slot;
      const out = await postOrder(
        {
          location_id: locationId,
          mode,
          pickup_at: pickupAt,
          items: items.map((it) => ({
            product_id: it.productId,
            option_ids: it.optionIds,
            quantity: it.qty,
          })),
          customer_name: customer.name.trim(),
          customer_phone: customer.phone.trim(),
          comment: customer.comment.trim(),
        },
        idempotencyKey,
      );
      customer.persist(customer.name.trim(), customer.phone.trim());
      addMyOrder({
        id: out.order.id,
        token: out.access_token,
        locationId,
        code: out.order.code,
        createdAt: Date.now(),
      });
      clear();
      nav(`/orders?fresh=${out.order.id}`);
    } catch (e) {
      const err = e as ApiError;
      if (err.code === "slot_unavailable") {
        await slotsQuery.refetch();
        setError(t.slotTaken);
      } else if (err.code === "product_unavailable" || err.code === "option_unavailable") {
        setError(t.productGone);
      } else if (err instanceof TypeError) {
        setError(t.offlineOrder);
      } else {
        setError(t.error);
      }
    } finally {
      setSending(false);
    }
  };

  return (
    <main className="mx-auto min-h-dvh w-full max-w-[480px] bg-panel pb-10 text-panel-text">
      <div className="flex items-center gap-3 px-5 pt-4 text-lg font-medium">
        <button
          type="button"
          onClick={() => nav(-1)}
          aria-label={t.back}
          className="grid h-9 w-9 place-items-center rounded-full"
        >
          ←
        </button>
        {t.checkoutTitle}
      </div>

      <div className="grid grid-cols-2 gap-2.5 px-5 pt-4">
        {(
          [
            { m: "on_site", title: t.modeHere, hint: t.modeHereHint },
            { m: "scheduled", title: t.modeLater, hint: t.modeLaterHint },
          ] as const
        ).map((o) => (
          <button
            key={o.m}
            type="button"
            aria-pressed={mode === o.m}
            onClick={() => setMode(o.m)}
            className={`flex flex-col items-center gap-1 rounded-tile p-3.5 text-[15px] font-semibold transition-colors ${
              mode === o.m
                ? "bg-[var(--panel-solid)] text-[var(--on-panel-solid)]"
                : "border border-[var(--panel-line)] bg-white"
            }`}
          >
            {o.title}
            <small
              className={`text-xs font-normal ${mode === o.m ? "opacity-70" : "text-panel-text-2"}`}
            >
              {o.hint}
            </small>
          </button>
        ))}
      </div>

      <section className="px-5 pt-3.5" aria-live="polite">
        {mode === "on_site" ? (
          <div>
            <h4 className="text-base font-semibold">{t.cookNow}</h4>
            <p className="text-[13px] text-panel-text-2">
              {asapLabel ? t.cookNowHint(10) : t.loading}
            </p>
          </div>
        ) : (
          <div>
            <h4 className="text-base font-semibold">{t.whenTake}</h4>
            <p className="text-[13px] text-panel-text-2">
              {t.today}. {asapLabel ? t.asapHint(asapLabel) : ""}
            </p>
            {slotsQuery.isLoading ? (
              <Skeleton className="mt-2.5 h-10" />
            ) : (
              <div className="mt-2.5 flex flex-wrap gap-2">
                <button
                  type="button"
                  aria-pressed={slot === "asap"}
                  onClick={() => setSlot("asap")}
                  className={`h-[38px] rounded-control border px-3 text-[13px] font-medium ${
                    slot === "asap"
                      ? "border-transparent bg-[var(--panel-solid)] text-[var(--on-panel-solid)]"
                      : "border-[var(--panel-line)] bg-white"
                  }`}
                >
                  {t.asapChip}
                </button>
                {(slots?.slots ?? []).map((s) => (
                  <button
                    key={s.start}
                    type="button"
                    disabled={!s.available}
                    aria-pressed={slot === s.start}
                    title={!s.available ? t.slotTaken : undefined}
                    onClick={() => setSlot(s.start)}
                    className={`h-[38px] rounded-control border px-3 text-[13px] font-medium tabular ${
                      slot === s.start
                        ? "border-transparent bg-[var(--panel-solid)] text-[var(--on-panel-solid)]"
                        : "border-[var(--panel-line)] bg-white disabled:opacity-40 disabled:line-through"
                    }`}
                  >
                    {slotLabel(s.start, timeZone)}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </section>

      <section className="px-5 pt-4">
        <h4 className="text-base font-semibold">{t.whoPicks}</h4>
        <label className="mt-2 block text-[13px] text-panel-text-2">
          {t.nameLabel}
          <input
            value={customer.name}
            onChange={(e) => customer.setName(e.target.value)}
            placeholder={t.namePlaceholder}
            autoComplete="name"
            className="mt-1 h-12 w-full rounded-input border border-[var(--panel-line)] bg-white px-3.5 text-base text-panel-text"
          />
        </label>
        {customer.touched && !customer.name.trim() ? (
          <p className="mt-1 text-xs text-danger">{t.nameRequired}</p>
        ) : null}
        <label className="mt-2.5 block text-[13px] text-panel-text-2">
          {t.phoneLabel}
          <input
            value={customer.phone}
            onChange={(e) => customer.setPhone(e.target.value)}
            placeholder={t.phonePlaceholder}
            inputMode="tel"
            autoComplete="tel"
            className="mt-1 h-12 w-full rounded-input border border-[var(--panel-line)] bg-white px-3.5 text-base tabular text-panel-text"
          />
        </label>
        {customer.touched && !isPhoneValid(customer.phone) ? (
          <p className="mt-1 text-xs text-danger">{t.phoneInvalid}</p>
        ) : null}
        <label className="mt-2.5 block text-[13px] text-panel-text-2">
          {t.commentLabel}
          <input
            value={customer.comment}
            onChange={(e) => customer.setComment(e.target.value)}
            placeholder={t.commentPlaceholder}
            className="mt-1 h-12 w-full rounded-input border border-[var(--panel-line)] bg-white px-3.5 text-base text-panel-text"
          />
        </label>
      </section>

      <section className="px-5 pt-4">
        <h4 className="text-base font-semibold">{t.yourOrder}</h4>
        <div className="mt-2 flex flex-col gap-2.5">
          {resolved.map((r) => (
            <div
              key={r.index}
              className="flex items-center gap-3 rounded-tile border border-[var(--panel-line)] bg-white p-3"
            >
              <span className="flex-1">
                <b className="block text-[15px] font-semibold">{r.name}</b>
                <Stepper label={r.name} value={r.item.qty} onChange={(v) => setQty(r.index, v)} />
              </span>
              <span className="flex flex-col items-end gap-1">
                <PriceText kopeks={r.line} className="text-[15px]" />
                <button
                  type="button"
                  onClick={() => removeAt(r.index)}
                  aria-label="Удалить"
                  className="text-xs text-panel-text-2"
                >
                  ✕
                </button>
              </span>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-3 mt-3.5 rounded-panel bg-[var(--panel-solid)] p-4 text-[var(--on-panel-solid)]">
        <div className="flex justify-between text-sm opacity-70">
          <span>{t.total}</span>
          <span className="tabular">{formatRub(subtotal)}</span>
        </div>
        <div className="mt-1 mb-3 flex items-baseline justify-between text-base">
          <span>{t.grandTotal}</span>
          <b className="tabular text-[22px] font-semibold">{formatRub(subtotal)}</b>
        </div>
        <div className="[&>button]:w-full">
          <Button loading={sending} onClick={() => void submit()}>
            {mode === "on_site" || slot === "asap"
              ? t.orderNowBtn
              : t.orderFor(slot && slot !== "asap" ? slotLabel(slot, timeZone) : (asapLabel ?? ""))}
          </Button>
        </div>
      </section>
      <p className="px-5 pt-3.5 text-xs text-panel-text-2">
        <b className="block text-[13px] text-panel-text">{t.payOnPickup}</b>
        {t.payLater}
      </p>

      <Toast
        message={error}
        actionLabel={error ? t.retry : undefined}
        onAction={error ? () => setError(null) : undefined}
      />
    </main>
  );
}
