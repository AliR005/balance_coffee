import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useQueries, useQueryClient } from "@tanstack/react-query";
import type { OrderOut } from "../../shared/api/generated/api";
import {
  getCancelOrderOrdersOrderIdCancelPostUrl,
  getGetOrderOrdersOrderIdGetUrl,
} from "../../shared/api/generated/api";
import { apiGet, apiPostEmpty } from "../../shared/api/base";
import { useT } from "../../shared/i18n";
import { Button } from "../../shared/ui/Button";
import { Chip } from "../../shared/ui/Chip";
import { Skeleton } from "../../shared/ui/Skeleton";
import { Splash } from "../../shared/ui/Splash";
import { TabBar } from "../../shared/ui/TabBar";
import { Toast } from "../../shared/ui/Toast";
import { useCart } from "../cart/store";
import { useMenu } from "../menu/api";
import { OrderCard } from "./OrderCard";
import { addMyOrder, myOrders, shouldSplash, type MyOrderRef } from "./registry";
import { rebuildOrder } from "./repeat";
import { useOrderStream } from "./useOrderStream";

const HISTORY = new Set(["picked_up", "cancelled"]);

async function fetchOrder(ref: MyOrderRef): Promise<OrderOut> {
  return apiGet<OrderOut>(
    `${getGetOrderOrdersOrderIdGetUrl(ref.id)}?token=${encodeURIComponent(ref.token)}`,
  );
}

function OrderSection({ orderRef, selected }: { orderRef: MyOrderRef; selected: boolean }) {
  const queryClient = useQueryClient();
  const t = useT();
  const [cancelling, setCancelling] = useState(false);
  const online = useOrderStream(orderRef.id, orderRef.token);
  const order = queryClient.getQueryData<OrderOut>(["order", orderRef.id]);

  const cancel = async () => {
    setCancelling(true);
    try {
      await apiPostEmpty(
        `${getCancelOrderOrdersOrderIdCancelPostUrl(orderRef.id)}?token=${encodeURIComponent(orderRef.token)}`,
      );
      await queryClient.invalidateQueries({ queryKey: ["order", orderRef.id] });
    } finally {
      setCancelling(false);
    }
  };

  if (!order) {
    return <Skeleton className="h-72" label={t.loading} />;
  }
  return (
    <div className={selected ? "rounded-panel ring-2 ring-[var(--primary)]" : ""}>
      <OrderCard
        order={order}
        online={online}
        cancelling={cancelling}
        onCancel={() => void cancel()}
      />
    </div>
  );
}

function RepeatButton({
  orderRef,
  order,
  onDone,
}: {
  orderRef: MyOrderRef;
  order: OrderOut | undefined;
  onDone: (msg: string) => void;
}) {
  const t = useT();
  const nav = useNavigate();
  const menuQuery = useMenu(orderRef.locationId);
  const addItem = useCart((s) => s.addItem);
  const setLocation = useCart((s) => s.setLocation);

  if (!order) return null;
  return (
    <Button
      variant="ghost"
      disabled={menuQuery.isLoading}
      onClick={() => {
        if (!menuQuery.data) return;
        const { ok, dropped } = rebuildOrder(menuQuery.data, order.items ?? []);
        if (ok.length === 0) {
          onDone(t.repeatDropped);
          return;
        }
        setLocation(orderRef.locationId, { clear: true });
        ok.forEach((it) => addItem(orderRef.locationId, it));
        onDone(dropped.length > 0 ? t.repeatDropped : t.added);
        nav("/checkout");
      }}
    >
      {t.repeat}
    </Button>
  );
}

/** Мой заказ: вкладки «Сейчас»/«История», SSE, отмена, повтор. */
export function OrdersPage() {
  const t = useT();
  const nav = useNavigate();
  const params = useParams();
  const [search] = useSearchParams();
  const [tab, setTab] = useState<"now" | "history">("now");
  const [refs, setRefs] = useState<MyOrderRef[]>(() => myOrders());
  const [toast, setToast] = useState<string | null>(null);
  const [splashId, setSplashId] = useState<number | null>(null);

  // Прямая ссылка /order/:id?t=… — подхватываем в реестр. Splash нового заказа — один раз.
  useEffect(() => {
    const id = Number(params.id ?? search.get("fresh") ?? NaN);
    const token = search.get("t");
    if (Number.isFinite(id) && token && !myOrders().some((r) => r.id === id)) {
      addMyOrder({ id, token, locationId: 0, code: "", createdAt: Date.now() });
      setRefs(myOrders());
    }
    if (Number.isFinite(id) && shouldSplash(id)) setSplashId(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(timer);
  }, [toast]);

  const snapshots = useQueries({
    queries: refs.map((r) => ({
      queryKey: ["order", r.id],
      queryFn: () => fetchOrder(r),
      refetchInterval: 15_000,
    })),
  });

  const byId = new Map<number, OrderOut>();
  snapshots.forEach((q, i) => {
    const ref = refs[i];
    if (q.data && ref) byId.set(ref.id, q.data);
  });
  const nowRefs = refs.filter((r) => !HISTORY.has(byId.get(r.id)?.status ?? ""));
  const historyRefs = refs.filter((r) => HISTORY.has(byId.get(r.id)?.status ?? ""));
  const shown = tab === "now" ? nowRefs : historyRefs;
  const lastRef = refs[0] ?? null;

  const goTab = (id: string) => {
    if (id === "menu") nav("/menu");
    else if (id === "bonus") nav("/bonus");
    else if (id === "profile") nav("/profile");
  };

  return (
    <main className="mx-auto min-h-dvh w-full max-w-[480px] bg-bg pb-28 text-text">
      {splashId !== null ? (
        <div
          className="fixed inset-0 z-50 grid place-items-center bg-bg"
          onClick={() => setSplashId(null)}
        >
          <Splash />
        </div>
      ) : null}

      <div className="flex items-center gap-3 px-5 pt-4">
        <button
          type="button"
          onClick={() => nav("/menu")}
          aria-label={t.back}
          className="grid h-9 w-9 place-items-center"
        >
          ←
        </button>
        <h1 className="text-lg font-medium">{t.ordersTitle}</h1>
      </div>

      <div className="flex gap-2 px-5 pt-3">
        <Chip pressed={tab === "now"} onClick={() => setTab("now")}>
          {t.tabNow}
        </Chip>
        <Chip pressed={tab === "history"} onClick={() => setTab("history")}>
          {t.tabHistory}
        </Chip>
      </div>

      {lastRef && byId.get(lastRef.id) ? (
        <div className="mx-5 mt-3 flex items-center gap-3 rounded-tile border border-[var(--line)] bg-surface p-3.5">
          <span className="flex-1 text-[13px]">
            <b className="block text-sm">{t.repeatLast}</b>
            {byId.get(lastRef.id)?.code}
          </span>
          <RepeatButton orderRef={lastRef} order={byId.get(lastRef.id)} onDone={setToast} />
        </div>
      ) : null}

      <div className="flex flex-col gap-4 p-5">
        {refs.length === 0 ? (
          <p className="py-10 text-center text-sm text-text-2">{t.noOrders}</p>
        ) : shown.length === 0 ? (
          <p className="py-10 text-center text-sm text-text-2">{t.noOrders}</p>
        ) : (
          shown.map((r) => <OrderSection key={r.id} orderRef={r} selected={r.id === splashId} />)
        )}
      </div>

      <Toast message={toast} />
      <TabBar
        active="orders"
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
