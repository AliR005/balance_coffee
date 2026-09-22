import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { apiBase } from "../../shared/api/base";

/** SSE одного заказа: автопереподключение с backoff. Возвращает online-флаг. */
export function useOrderStream(id: number, token: string): boolean {
  const queryClient = useQueryClient();
  const [online, setOnline] = useState(true);

  useEffect(() => {
    let es: EventSource | null = null;
    let closed = false;
    let timer = 0;
    let retries = 0;

    const connect = () => {
      if (closed) return;
      es = new EventSource(`${apiBase()}/orders/${id}/events?token=${encodeURIComponent(token)}`);
      es.onopen = () => {
        setOnline(true);
        retries = 0;
        void queryClient.invalidateQueries({ queryKey: ["order", id] });
      };
      es.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data) as { type?: string; order?: unknown };
          if (msg.type === "snapshot" && msg.order) {
            queryClient.setQueryData(["order", id], msg.order);
          } else if (msg.type === "status") {
            void queryClient.invalidateQueries({ queryKey: ["order", id] });
          }
        } catch {
          /* игнорируем битые кадры */
        }
      };
      es.onerror = () => {
        setOnline(false);
        es?.close();
        const backoff = Math.min(1000 * 2 ** retries, 15_000);
        retries += 1;
        timer = window.setTimeout(connect, backoff);
      };
    };

    connect();
    return () => {
      closed = true;
      window.clearTimeout(timer);
      es?.close();
    };
  }, [id, token, queryClient]);

  return online;
}
