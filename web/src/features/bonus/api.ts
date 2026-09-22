import { useQuery } from "@tanstack/react-query";
import type { AccountOut, TransactionOut } from "../../shared/api/generated/api";
import { apiGet } from "../../shared/api/base";
import { myOrders } from "../orders/registry";

/** Учётные данные гостя для бонусов: телефон из формы, токен последнего заказа. */
export function bonusCreds(): { phone: string; token: string } | null {
  const phone = localStorage.getItem("balance-customer-phone") ?? "";
  const token = myOrders()[0]?.token ?? "";
  if ((phone.match(/\d/g) ?? []).length < 5 || !token) return null;
  return { phone, token };
}

export function useBonusAccount(phoneOverride?: string) {
  const creds = bonusCreds();
  const phone = phoneOverride ?? creds?.phone ?? "";
  const token = creds?.token ?? "";
  const enabled = (phone.match(/\d/g) ?? []).length >= 5 && token !== "";
  return useQuery({
    queryKey: ["bonus-account", phone],
    queryFn: () =>
      apiGet<AccountOut>(
        `/bonus/account?phone=${encodeURIComponent(phone)}&token=${encodeURIComponent(token)}`,
      ),
    enabled,
    retry: false,
  });
}

export function useBonusTransactions() {
  const creds = bonusCreds();
  return useQuery({
    queryKey: ["bonus-txns", creds?.phone],
    queryFn: () =>
      apiGet<TransactionOut[]>(
        `/bonus/transactions?phone=${encodeURIComponent(creds?.phone ?? "")}&token=${encodeURIComponent(creds?.token ?? "")}`,
      ),
    enabled: creds !== null,
    retry: false,
  });
}
