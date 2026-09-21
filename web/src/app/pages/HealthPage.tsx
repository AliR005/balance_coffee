import { useQuery } from "@tanstack/react-query";
import { getHealthHealthGetUrl } from "../../shared/api/generated/api";
import { useT } from "../../shared/i18n";

async function fetchHealth(): Promise<string> {
  const base = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
  const res = await fetch(`${base}${getHealthHealthGetUrl()}`);
  if (!res.ok) throw new Error(`health failed: ${res.status}`);
  const data = (await res.json()) as { status?: string };
  return data.status ?? "ok";
}

export function HealthPage() {
  const t = useT();
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
  });

  return (
    <main className="min-h-screen bg-bg text-text flex flex-col items-center justify-center gap-4 p-5">
      <h1 className="text-2xl font-medium">balance</h1>
      {isLoading && <p>{t.loading}</p>}
      {isError && (
        <div className="flex flex-col items-center gap-2">
          <p>{t.error}</p>
          <button
            type="button"
            onClick={() => void refetch()}
            className="rounded-control bg-primary px-4 py-2 text-on-primary min-h-[44px]"
          >
            {t.retry}
          </button>
        </div>
      )}
      {data && <p>API: {data}</p>}
    </main>
  );
}
