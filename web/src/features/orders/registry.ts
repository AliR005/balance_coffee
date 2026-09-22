export interface MyOrderRef {
  id: number;
  token: string;
  locationId: number;
  code: string;
  createdAt: number;
}

const KEY = "balance-my-orders";
const MAX = 20;

function read(): MyOrderRef[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const arr = JSON.parse(raw) as MyOrderRef[];
    return Array.isArray(arr) ? arr : [];
  } catch {
    return [];
  }
}

function write(refs: MyOrderRef[]): void {
  localStorage.setItem(KEY, JSON.stringify(refs.slice(0, MAX)));
}

/** Токены заказов гостя. Передаются в ссылке /order/:id?t=… */
export function myOrders(): MyOrderRef[] {
  return read();
}

export function addMyOrder(ref: MyOrderRef): void {
  write([ref, ...read().filter((r) => r.id !== ref.id)]);
}

export function dropMyOrder(id: number): void {
  write(read().filter((r) => r.id !== id));
}

/** Splash нового заказа — один раз. */
export function shouldSplash(id: number): boolean {
  const key = `balance-splash-${id}`;
  if (sessionStorage.getItem(key)) return false;
  sessionStorage.setItem(key, "1");
  return true;
}
