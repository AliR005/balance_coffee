import "@testing-library/jest-dom/vitest";

// В этом окружении jsdom отдаёт localStorage без методов — подменяем памятью.
const mem = new Map<string, string>();
Object.defineProperty(globalThis, "localStorage", {
  value: {
    getItem: (k: string) => mem.get(k) ?? null,
    setItem: (k: string, v: string) => {
      mem.set(k, v);
    },
    removeItem: (k: string) => {
      mem.delete(k);
    },
    clear: () => mem.clear(),
    get length() {
      return mem.size;
    },
    key: (i: number) => [...mem.keys()][i] ?? null,
  },
  configurable: true,
  writable: true,
});
