import type { OrderOut } from "../../shared/api/generated/api";
import { useT } from "../../shared/i18n";
import { formatRub } from "../../shared/lib/format";
import { BrewVideo } from "../../shared/ui/BrewVideo";
import type { BrewVariant } from "../../shared/ui/BrewView";
import { Button } from "../../shared/ui/Button";
import { PriceText } from "../../shared/ui/PriceText";

interface Props {
  order: OrderOut;
  variant?: BrewVariant;
  online: boolean;
  cancelling: boolean;
  onCancel: () => void;
}

function stageIndex(status: string): number {
  switch (status) {
    case "confirmed":
      return 0;
    case "preparing":
      return 1;
    case "ready":
    case "picked_up":
      return 2;
    default:
      return 0;
  }
}

/** Карточка заказа: ролик, код, статус, линия стадий, состав, отмена. */
export function OrderCard({ order, variant = "heart", online, cancelling, onCancel }: Props) {
  const t = useT();
  const stage = stageIndex(order.status);
  const productName = order.items?.[0]?.product_name ?? "";
  const time = new Date(order.pickup_at).toLocaleTimeString("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
  });

  const statusTitle =
    order.status === "confirmed"
      ? t.statusConfirmed
      : order.status === "preparing"
        ? t.statusPreparing
        : order.status === "ready"
          ? t.statusReady
          : order.status === "picked_up"
            ? t.statusPickedUp
            : t.statusCancelled;

  return (
    <article className="overflow-hidden rounded-panel border border-[var(--line)] bg-surface">
      <div className="relative h-[210px] bg-[radial-gradient(70%_60%_at_50%_45%,var(--glow),transparent_72%),linear-gradient(var(--surface-2),var(--bg))]">
        <BrewVideo
          variant={variant}
          durationSec={9}
          className="absolute top-3.5 left-1/2 w-[172px] -translate-x-1/2 drop-shadow-[0_12px_16px_rgb(0_0_0/.6)]"
          title={productName}
        />
        <span className="absolute bottom-3 left-3.5 rounded-[14px] border border-[var(--line)] bg-[var(--glass-bg)] px-2.5 py-1 text-xs backdrop-blur">
          {t.cookingCaption(productName || "кофе")}
        </span>
        {!online ? (
          <span className="absolute top-3 right-3.5 rounded-[14px] bg-[var(--surface-3)] px-2.5 py-1 text-xs text-text-2">
            {t.offlineBadge}
          </span>
        ) : null}
      </div>

      <div className="p-4">
        <div className="flex items-baseline justify-between">
          <b className="tabular text-[34px] leading-none font-semibold tracking-tight">
            {order.code}
          </b>
          <span className="text-[13px] text-text-2">{time}</span>
        </div>
        <h4 className="mt-1.5 text-lg font-medium text-accent-text">{statusTitle}</h4>
        <p className="text-[13px] text-text-2">{t.pickupAt(time)}</p>

        <div className="mt-4 flex items-center" aria-label="Стадии заказа">
          {[0, 1, 2].map((i) => (
            <span key={i} className="flex flex-1 items-center last:flex-none">
              <span
                className={`h-3.5 w-3.5 rounded-full ${i < stage ? "bg-[var(--primary)]" : i === stage ? "border-4 border-[var(--primary)] bg-[var(--bg)]" : "bg-[var(--surface-3)]"}`}
              />
              {i < 2 ? (
                <span
                  className={`mx-0.5 h-[3px] flex-1 rounded ${i + 1 <= stage ? "bg-[var(--primary)]" : "bg-[var(--surface-3)]"}`}
                />
              ) : null}
            </span>
          ))}
        </div>
        <div className="mt-1.5 flex justify-between text-xs text-text-2">
          <span className={stage === 0 ? "font-semibold text-text" : ""}>{t.stageAccepted}</span>
          <span className={stage === 1 ? "font-semibold text-text" : ""}>{t.stageCooking}</span>
          <span className={stage === 2 ? "font-semibold text-text" : ""}>{t.stageReady}</span>
        </div>

        <div className="mt-3 flex flex-col gap-2">
          {(order.items ?? []).map((it, k) => (
            <div key={k} className="flex justify-between gap-3 text-sm">
              <span>
                <b className="font-semibold">
                  {it.product_name}, {it.quantity}
                </b>
                <small className="block text-xs text-text-2">
                  {(it.options ?? []).map((o) => (o as { option?: string }).option).join(" · ")}
                </small>
              </span>
              <PriceText kopeks={it.line_total} />
            </div>
          ))}
        </div>
        <p className="mt-2 text-[13px] text-success">
          {t.bonusPlus(Math.floor((order.total / 100) * 0.05))}. {t.bonusSoonText}
        </p>

        {order.status === "confirmed" ? (
          <div className="mt-3">
            <Button variant="ghost" loading={cancelling} onClick={onCancel}>
              {t.cancelOrder}
            </Button>
          </div>
        ) : (
          <p className="mt-3 text-center text-xs text-text-2">{t.cancelImpossible}</p>
        )}
        <p className="tabular mt-2 text-right text-sm text-text-2">{formatRub(order.total)}</p>
      </div>
    </article>
  );
}
