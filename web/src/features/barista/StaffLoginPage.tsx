import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useT } from "../../shared/i18n";
import { Button } from "../../shared/ui/Button";
import { Skeleton } from "../../shared/ui/Skeleton";
import { useLocations } from "../menu/api";
import { staffLogin } from "./api";

/** Вход баристы: точка + PIN. */
export function StaffLoginPage() {
  const t = useT();
  const nav = useNavigate();
  const locQuery = useLocations();
  const [locationId, setLocationId] = useState<number | null>(null);
  const [pin, setPin] = useState("");
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (locationId === null || pin.length < 4) return;
    setBusy(true);
    setError(false);
    try {
      await staffLogin(locationId, pin);
      nav("/staff/board");
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-[480px] flex-col justify-center gap-4 bg-bg p-6 text-text">
      <h2 className="text-[30px] font-normal">{t.staffLogin}</h2>
      {locQuery.isLoading ? (
        <Skeleton className="h-14" />
      ) : (
        <label className="text-sm text-text-2">
          {t.chooseLocation}
          <select
            value={locationId ?? ""}
            onChange={(e) => setLocationId(Number(e.target.value))}
            className="mt-1 h-14 w-full rounded-input border border-[var(--line-strong)] bg-surface px-3.5 text-base text-text"
          >
            <option value="" disabled>
              —
            </option>
            {locQuery.data?.map((l) => (
              <option key={l.id} value={l.id}>
                {l.name}
              </option>
            ))}
          </select>
        </label>
      )}
      <label className="text-sm text-text-2">
        PIN
        <input
          value={pin}
          onChange={(e) => setPin(e.target.value.replace(/\D/g, "").slice(0, 8))}
          inputMode="numeric"
          type="password"
          autoComplete="off"
          className="tabular mt-1 h-14 w-full rounded-input border border-[var(--line-strong)] bg-surface px-3.5 text-center text-2xl tracking-[0.5em] text-text"
        />
      </label>
      {error ? <p className="text-sm text-danger">{t.staffLoginError}</p> : null}
      <Button loading={busy} onClick={() => void submit()}>
        {t.staffEnter}
      </Button>
    </main>
  );
}
