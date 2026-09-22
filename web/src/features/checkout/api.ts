import { useQuery } from "@tanstack/react-query";
import {
  getCreateOrderOrdersPostUrl,
  getSlotsLocationsLocationIdSlotsGetUrl,
  type OrderCreateIn,
  type OrderCreateOut,
  type SlotsOut,
} from "../../shared/api/generated/api";
import { apiGet, apiPost } from "../../shared/api/base";

/** Слоты точки на сегодня + оценка «как можно скорее». */
export function useSlots(locationId: number | null, units: number) {
  return useQuery({
    queryKey: ["slots", locationId, units],
    queryFn: () =>
      apiGet<SlotsOut>(`${getSlotsLocationsLocationIdSlotsGetUrl(locationId ?? 0)}?units=${units}`),
    enabled: locationId !== null && units > 0,
    refetchInterval: 30_000,
  });
}

/** Создание заказа. Ключ идемпотентности передаёт вызывающий. */
export function postOrder(body: OrderCreateIn, idempotencyKey: string): Promise<OrderCreateOut> {
  return apiPost<OrderCreateOut>(getCreateOrderOrdersPostUrl(), body, {
    headers: { "Idempotency-Key": idempotencyKey },
  });
}

/** Новый ключ на открытие экрана оформления. */
export function newIdempotencyKey(): string {
  return crypto.randomUUID();
}
