import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import type { OrderOut } from "../../shared/api/generated/api";
import { useT } from "../../shared/i18n";
import { apiBase } from "../../shared/api/base";
import { Button } from "../../shared/ui/Button";
import { Toast } from "../../shared/ui/Toast";
import { changeStatus, clearSession, loadSession, useStaffOrders } from "./api";
import { playNewOrderSound, setSoundEnabled, soundEnabled } from "./sound";
import { nextAction, sortBoard, urgencyOf } from "./urgency";
import { useWakeLock } from "./wakelock";

function timeLabel(iso: string): string {
  return new Date(iso).toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
}

function OrderCardBarista({
  order,
  flash,
  onAction,
  busy,
}: {
  order: OrderOut;
  flash: boolean;
  onAction: (to: string) => void;
  busy: boolean;
}) {
  const t = useT();
  const [confirmCancel, setConfirmCancel] = useState(false);
  const u = urgencyOf(order.pickup_at, Date.now());
  const action = nextAction(order.status);
  const urgencyText = u.overdue
    ? t.overdue
    : u.level === "soon"
      ? t.dueSoon(u.mins)
      : t.dueIn(u.mins);

  return (
    <article
      className={`rounded-tile border bg-surface p-4 ${flash ? "border-[var(--primary)]" : "border-[var(--line)]"}`}
    >
      <div className="flex items-baseline justify-between gap-2">
        <b className="tabular text-2xl font-semibold whitespace-nowrap">{order.code}</b>
        <span
          className={`tabular text-sm font-semibold ${u.overdue ? "text-danger" : u.level === "soon" ? "text-accent-text" : "text-text-2"}`}
        >
          {order.mode === "on_site" ? t.modeHere : t.toServe(timeLabel(order.pickup_at))} ·{" "}
          {urgencyText}
        </span>
      </div>
      <p className="mt-0.5 text-sm text-text-2">{order.customer_name}</p>
      <div className="mt-2 flex flex-col gap-1.5 text-[15px]">
        {order.items?.map((it, k) => (
          <div key={k}>
            <b className="font-semibold">
              {it.product_name} × {it.quantity}
            </b>
            {(it.options ?? []).map((o, j) => (
              <small key={j} className="block text-[13px] text-text-2">
                {(o as { option?: string }).option}
              </small>
            ))}
          </div>
        ))}
      </div>
      {order.comment ? (
        <p className="mt-2 text-base font-medium text-accent-text">{order.comment}</p>
      ) : null}
      <div className="mt-3 flex flex-col gap-2">
        {action ? (
          <button
            type="button"
            disabled={busy}
            onClick={() => onAction(action.to)}
            className="h-16 rounded-tile bg-[var(--primary)] text-lg font-semibold text-on-primary disabled:opacity-50"
          >
            {action.label}
          </button>
        ) : null}
        {order.status === "confirmed" || order.status === "preparing" ? (
          confirmCancel ? (
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => onAction("cancelled")}
                className="h-12 flex-1 rounded-tile border border-[var(--danger)] text-danger"
              >
                {t.confirmYes}
              </button>
              <button
                type="button"
                onClick={() => setConfirmCancel(false)}
                className="h-12 flex-1 rounded-tile border border-[var(--line-strong)]"
              >
                {t.confirmNo}
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setConfirmCancel(true)}
              className="h-12 rounded-tile border border-[var(--line-strong)] text-text-2"
            >
              {t.cancelOrder}
            </button>
          )
        ) : null}
      </div>
    </article>
  );
}

/** Доска баристы: три колонки, SSE, звук, wake lock. */
export function BoardPage() {
  const t = useT();
  const nav = useNavigate();
  const queryClient = useQueryClient();
  const [session, setSession] = useState(loadSession);
  const [online, setOnline] = useState(true);
  const [sound, setSound] = useState(soundEnabled());
  const [flashes, setFlashes] = useState<Set<number>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const knownRef = useRef<Set<number>>(new Set());
  useWakeLock(session !== null);

  useEffect(() => {
    if (!session) nav("/staff");
  }, [session, nav]);

  const ordersQuery = useStaffOrders(session?.token ?? null);

  // SSE доски: снапшот при переподключении (полная пересинхронизация).
  useEffect(() => {
    if (!session) return;
    let es: EventSource | null = null;
    let closed = false;
    let timer = 0;
    const connect = () => {
      if (closed) return;
      es = new EventSource(
        `${apiBase()}/staff/orders/stream?token=${encodeURIComponent(session.token)}`,
      );
      es.onopen = () => {
        setOnline(true);
        void queryClient.invalidateQueries({ queryKey: ["staff-orders"] });
      };
      es.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data) as { type?: string; order_id?: number };
          if (msg.type === "order_created" && typeof msg.order_id === "number") {
            if (!knownRef.current.has(msg.order_id)) {
              playNewOrderSound();
              setFlashes((f) => new Set(f).add(msg.order_id as number));
              window.setTimeout(() => {
                setFlashes((f) => {
                  const n = new Set(f);
                  n.delete(msg.order_id as number);
                  return n;
                });
              }, 10_000);
            }
          }
          void queryClient.invalidateQueries({ queryKey: ["staff-orders"] });
        } catch {
          /* игнорируем */
        }
      };
      es.onerror = () => {
        setOnline(false);
        es?.close();
        timer = window.setTimeout(connect, 3000);
      };
    };
    connect();
    return () => {
      closed = true;
      window.clearTimeout(timer);
      es?.close();
    };
  }, [session, queryClient]);

  useEffect(() => {
    const ids = new Set((ordersQuery.data ?? []).map((o) => o.id));
    knownRef.current = ids;
  }, [ordersQuery.data]);

  if (!session) return null;

  const orders = sortBoard(ordersQuery.data ?? []);
  const cols: { key: string; title: string; list: OrderOut[] }[] = [
    { key: "confirmed", title: t.colNew, list: orders.filter((o) => o.status === "confirmed") },
    { key: "preparing", title: t.colCooking, list: orders.filter((o) => o.status === "preparing") },
    { key: "ready", title: t.colReady, list: orders.filter((o) => o.status === "ready") },
  ];

  const act = async (order: OrderOut, to: string) => {
    if (!session) return;
    setBusyId(order.id);
    // Оптимистично — с откатом при ошибке.
    const prev = queryClient.getQueryData<OrderOut[]>(["staff-orders"]);
    queryClient.setQueryData<OrderOut[]>(["staff-orders"], (old) =>
      (old ?? []).map((o) => (o.id === order.id ? { ...o, status: to } : o)),
    );
    try {
      await changeStatus(session.token, order.id, to);
      await queryClient.invalidateQueries({ queryKey: ["staff-orders"] });
    } catch {
      queryClient.setQueryData(["staff-orders"], prev);
      setError(t.error);
    } finally {
      setBusyId(null);
    }
  };

  return (
    <main className="min-h-dvh bg-bg p-4 text-text lg:p-6">
      <header className="mx-auto flex max-w-6xl flex-wrap items-center gap-2">
        <h1 className="mr-auto text-xl font-semibold">{t.board}</h1>
        <span className={`text-xs ${online ? "text-success" : "text-danger"}`}>
          {online ? t.online : t.offlineBadge}
        </span>
        <button
          type="button"
          onClick={() => {
            const next = !sound;
            setSound(next);
            setSoundEnabled(next);
          }}
          aria-pressed={sound}
          className="h-11 rounded-control border border-[var(--line-strong)] px-3.5 text-sm"
        >
          {sound ? t.soundOn : t.soundOff}
        </button>
        <button
          type="button"
          onClick={() => nav("/staff/stop")}
          className="h-11 rounded-control border border-[var(--line-strong)] px-3.5 text-sm"
        >
          {t.stopList}
        </button>
        <button
          type="button"
          onClick={() => {
            clearSession();
            setSession(null);
          }}
          className="h-11 rounded-control border border-[var(--line-strong)] px-3.5 text-sm text-text-2"
        >
          {t.staffExit}
        </button>
      </header>

      {ordersQuery.isLoading ? (
        <p className="mx-auto max-w-6xl py-10 text-text-2">{t.loading}</p>
      ) : (
        <div className="mx-auto mt-4 grid max-w-6xl gap-4 md:grid-cols-3">
          {cols.map((c) => (
            <section key={c.key} aria-label={c.title}>
              <h2 className="mb-2 text-sm font-semibold text-text-2">
                {c.title} · {c.list.length}
              </h2>
              <div className="flex flex-col gap-3">
                {c.list.map((o) => (
                  <OrderCardBarista
                    key={o.id}
                    order={o}
                    flash={flashes.has(o.id)}
                    busy={busyId === o.id}
                    onAction={(to) => void act(o, to)}
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
      {error ? <Toast message={error} /> : null}
      <div className="mx-auto max-w-6xl pt-4">
        <Button variant="ghost" onClick={() => void ordersQuery.refetch()}>
          {t.retry}
        </Button>
      </div>
    </main>
  );
}
