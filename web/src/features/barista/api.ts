import { useQuery } from "@tanstack/react-query";
import type { OrderOut } from "../../shared/api/generated/api";
import { apiGet, apiPost, apiPut } from "../../shared/api/base";

function auth(token: string): RequestInit {
  return { headers: { Authorization: `Bearer ${token}` } };
}

export interface StaffSession {
  token: string;
  locationId: number;
  expiresAt: number;
}

const KEY = "balance-staff";

export function loadSession(): StaffSession | null {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const s = JSON.parse(raw) as StaffSession;
    if (!s.token || s.expiresAt * 1000 < Date.now()) return null;
    return s;
  } catch {
    return null;
  }
}

export function saveSession(s: StaffSession): void {
  localStorage.setItem(KEY, JSON.stringify(s));
}

export function clearSession(): void {
  localStorage.removeItem(KEY);
}

export async function staffLogin(locationId: number, pin: string): Promise<StaffSession> {
  const out = await apiPost<{ token: string; location_id: number; expires_at: number }>(
    "/staff/login",
    { location_id: locationId, pin },
  );
  const session = { token: out.token, locationId: out.location_id, expiresAt: out.expires_at };
  saveSession(session);
  return session;
}

export function useStaffOrders(token: string | null) {
  return useQuery({
    queryKey: ["staff-orders"],
    queryFn: () => apiGet<OrderOut[]>("/staff/orders", auth(token ?? "")),
    enabled: token !== null,
    refetchInterval: 30_000,
  });
}

export function changeStatus(token: string, orderId: number, to: string): Promise<OrderOut> {
  return apiPost<OrderOut>(`/staff/orders/${orderId}/status`, { to_status: to }, auth(token));
}

export interface Availability {
  location_id: number;
  products: { id: number; name: string; available?: boolean }[];
  options: { id: number; name: string; group: string; available?: boolean }[];
}

export function useAvailability(token: string | null) {
  return useQuery({
    queryKey: ["staff-availability"],
    queryFn: () => apiGet<Availability>("/staff/availability", auth(token ?? "")),
    enabled: token !== null,
  });
}

export function setProductAvailable(
  token: string,
  id: number,
  available: boolean,
): Promise<unknown> {
  return apiPut(`/staff/availability/products/${id}`, { is_available: available }, auth(token));
}

export function setOptionAvailable(
  token: string,
  id: number,
  available: boolean,
): Promise<unknown> {
  return apiPut(`/staff/availability/options/${id}`, { is_available: available }, auth(token));
}
