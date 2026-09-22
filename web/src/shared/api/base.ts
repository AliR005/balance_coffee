const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export function apiBase(): string {
  return BASE;
}

export interface ApiError extends Error {
  status: number;
  code?: string;
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) throw await toApiError(res, `GET ${path}`);
  return (await res.json()) as T;
}

export async function apiPost<T>(path: string, body: unknown, init?: RequestInit): Promise<T> {
  const { headers, ...rest } = init ?? {};
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    body: JSON.stringify(body),
    ...rest,
    headers: { "Content-Type": "application/json", ...(headers ?? {}) },
  });
  if (!res.ok) throw await toApiError(res, `POST ${path}`);
  return (await res.json()) as T;
}

/** POST без тела (например, отмена заказа — лишнее тело даст 422). */
export async function apiPostEmpty<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: "POST", ...init });
  if (!res.ok) throw await toApiError(res, `POST ${path}`);
  return (await res.json()) as T;
}

/** PUT с JSON-телом. */
export async function apiPut<T>(path: string, body: unknown, init?: RequestInit): Promise<T> {
  const { headers, ...rest } = init ?? {};
  const res = await fetch(`${BASE}${path}`, {
    method: "PUT",
    body: JSON.stringify(body),
    ...rest,
    headers: { "Content-Type": "application/json", ...(headers ?? {}) },
  });
  if (!res.ok) throw await toApiError(res, `PUT ${path}`);
  return (await res.json()) as T;
}

async function toApiError(res: Response, fallback: string): Promise<ApiError> {
  let code: string | undefined;
  try {
    const data = (await res.json()) as { code?: string };
    code = data.code;
  } catch {
    /* тело не JSON — оставляем статус */
  }
  const err = new Error(`${fallback} failed: ${res.status}`) as ApiError;
  err.status = res.status;
  err.code = code;
  return err;
}
