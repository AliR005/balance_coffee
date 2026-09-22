import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { useT } from "../../shared/i18n";
import { Button } from "../../shared/ui/Button";
import { Skeleton } from "../../shared/ui/Skeleton";
import { Switch } from "../../shared/ui/Switch";
import { loadSession, setOptionAvailable, setProductAvailable, useAvailability } from "./api";

/** Стоп-лист точки: напитки и опции с переключателями. */
export function StoplistPage() {
  const t = useT();
  const nav = useNavigate();
  const queryClient = useQueryClient();
  const [session] = useState(loadSession);
  const [error, setError] = useState<string | null>(null);

  const availQuery = useAvailability(session?.token ?? null);

  if (!session) {
    nav("/staff");
    return null;
  }

  const toggle = async (kind: "p" | "o", id: number, current: boolean) => {
    try {
      if (kind === "p") await setProductAvailable(session.token, id, !current);
      else await setOptionAvailable(session.token, id, !current);
      await queryClient.invalidateQueries({ queryKey: ["staff-availability"] });
    } catch {
      setError(t.error);
    }
  };

  return (
    <main className="mx-auto min-h-dvh w-full max-w-3xl bg-bg p-4 text-text lg:p-6">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => nav("/staff/board")}
          aria-label={t.back}
          className="grid h-11 w-11 place-items-center rounded-full border border-[var(--line-strong)]"
        >
          ←
        </button>
        <h1 className="text-xl font-semibold">{t.stopList}</h1>
      </div>

      {availQuery.isLoading ? (
        <Skeleton className="mt-4 h-40" />
      ) : (
        <>
          <h2 className="mt-5 mb-1 text-sm font-semibold text-text-2">{t.stopDrinks}</h2>
          <div className="flex flex-col gap-1">
            {(availQuery.data?.products ?? []).map((p) => (
              <div
                key={p.id}
                className={`flex items-center gap-3 rounded-tile border p-3.5 ${p.available === false ? "border-[var(--danger)] opacity-70" : "border-[var(--line)]"}`}
              >
                <span className="flex-1 text-[15px] font-medium">
                  {p.name}
                  {p.available === false ? (
                    <small className="block text-xs text-danger">{t.soldOut}</small>
                  ) : null}
                </span>
                <Switch
                  label={p.name}
                  checked={p.available !== false}
                  onChange={() => void toggle("p", p.id, p.available !== false)}
                />
              </div>
            ))}
          </div>
          <h2 className="mt-5 mb-1 text-sm font-semibold text-text-2">{t.stopOptions}</h2>
          <div className="flex flex-col gap-1">
            {(availQuery.data?.options ?? []).map((o) => (
              <div
                key={o.id}
                className={`flex items-center gap-3 rounded-tile border p-3.5 ${o.available === false ? "border-[var(--danger)] opacity-70" : "border-[var(--line)]"}`}
              >
                <span className="flex-1 text-[15px]">
                  {o.name} <small className="text-xs text-text-2">· {o.group}</small>
                </span>
                <Switch
                  label={o.name}
                  checked={o.available !== false}
                  onChange={() => void toggle("o", o.id, o.available !== false)}
                />
              </div>
            ))}
          </div>
        </>
      )}
      {error ? (
        <div className="pt-4">
          <Button variant="ghost" onClick={() => setError(null)}>
            {t.retry}
          </Button>
        </div>
      ) : null}
    </main>
  );
}
