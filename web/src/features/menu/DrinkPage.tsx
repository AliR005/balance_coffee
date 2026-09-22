import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import type { ProductOut } from "../../shared/api/generated/api";
import { useT } from "../../shared/i18n";
import { BrewView } from "../../shared/ui/BrewView";
import { Button } from "../../shared/ui/Button";
import { Chip } from "../../shared/ui/Chip";
import { DrinkPlayer } from "../../shared/ui/DrinkPlayer";
import { PriceText } from "../../shared/ui/PriceText";
import { SizeButtons } from "../../shared/ui/SizeButtons";
import { Skeleton } from "../../shared/ui/Skeleton";
import { Toast } from "../../shared/ui/Toast";
import { formatRub } from "../../shared/lib/format";
import type { VideoStep } from "../../shared/lib/steps";
import { useCart } from "../cart/store";
import { useMenu } from "./api";
import { brewVariantOf, selectedMilkColor } from "./brew";
import {
  bonusPreview,
  computePrice,
  defaultSelection,
  missingRequiredGroups,
  selectionDeltas,
} from "./pricing";

function stepsOf(product: ProductOut): VideoStep[] {
  if (!Array.isArray(product.video_steps)) return [];
  return product.video_steps.flatMap((s) => {
    if (typeof s !== "object" || s === null) return [];
    const r = s as Record<string, unknown>;
    const title = typeof r["title"] === "string" ? r["title"] : null;
    const at =
      typeof r["at_sec"] === "number"
        ? r["at_sec"]
        : typeof r["atSec"] === "number"
          ? r["atSec"]
          : 0;
    return title ? [{ title, atSec: at }] : [];
  });
}

function sizeScale(product: ProductOut, selection: Record<number, number[]>): number {
  for (const g of product.groups ?? []) {
    if (g.key !== "size") continue;
    const chosen = (selection[g.id] ?? [])[0];
    const name = (g.options ?? []).find((o) => o.id === chosen)?.name ?? "";
    if (name.startsWith("S")) return 0.9;
    if (name.startsWith("L")) return 1.08;
  }
  return 1;
}

/** Экран напитка: ролик, состав, живая цена и чашка. */
export function DrinkPage() {
  const t = useT();
  const nav = useNavigate();
  const { id } = useParams();
  const productId = Number(id);
  const locationId = useCart((s) => s.locationId);
  const addItem = useCart((s) => s.addItem);

  const menuQuery = useMenu(locationId);
  const product = useMemo(
    () =>
      menuQuery.data?.categories
        ?.flatMap((c) => c.products ?? [])
        .find((p) => p.id === productId) ?? null,
    [menuQuery.data, productId],
  );

  const [selection, setSelection] = useState<Record<number, number[]>>({});
  const [highlight, setHighlight] = useState<number[]>([]);
  const [toast, setToast] = useState<string | null>(null);
  const groupRefs = useRef(new Map<number, HTMLDivElement>());

  useEffect(() => {
    if (product) setSelection(defaultSelection(product));
  }, [product?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 2000);
    return () => clearTimeout(timer);
  }, [toast]);

  if (menuQuery.isLoading) {
    return (
      <main className="mx-auto w-full max-w-[480px] bg-bg" role="status" aria-label={t.loading}>
        <Skeleton className="h-[340px] rounded-none" />
        <div className="space-y-3 p-5">
          <Skeleton className="h-8 w-2/3" />
          <Skeleton className="h-14" />
        </div>
      </main>
    );
  }

  if (menuQuery.isError || !product) {
    return (
      <main className="mx-auto flex min-h-dvh w-full max-w-[480px] flex-col items-center justify-center gap-3 bg-bg p-10 text-center text-text">
        <p className="text-sm text-text-2">{t.error}</p>
        <Button variant="ghost" onClick={() => void menuQuery.refetch()}>
          {t.retry}
        </Button>
      </main>
    );
  }

  if (product.available === false) {
    return (
      <main className="mx-auto flex min-h-dvh w-full max-w-[480px] flex-col items-center justify-center gap-3 bg-bg p-10 text-center text-text">
        <p className="text-sm text-text-2">{t.soldOut}</p>
        <Button variant="ghost" onClick={() => nav(-1)}>
          {t.back}
        </Button>
      </main>
    );
  }

  const flatOptionIds = Object.values(selection).flat();
  const deltas = selectionDeltas(product, flatOptionIds);
  const price = computePrice(product.base_price, deltas, 1);
  const bonus = bonusPreview(price);
  const missing = missingRequiredGroups(product, selection);
  const milkColor = selectedMilkColor(product, flatOptionIds);

  const toggle = (groupId: number, optionId: number, max: number) => {
    setSelection((s) => {
      const cur = s[groupId] ?? [];
      const next =
        max === 1
          ? [optionId]
          : cur.includes(optionId)
            ? cur.filter((o) => o !== optionId)
            : [...cur, optionId].slice(0, max);
      return { ...s, [groupId]: next };
    });
    setHighlight((h) => h.filter((g) => g !== groupId));
  };

  const submit = () => {
    if (missing.length > 0) {
      setHighlight(missing);
      const first = groupRefs.current.get(missing[0] ?? -1);
      first?.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    if (locationId !== null) {
      addItem(locationId, { productId: product.id, optionIds: flatOptionIds, qty: 1 });
      setToast(t.added);
    }
  };

  return (
    <main className="mx-auto min-h-dvh w-full max-w-[480px] bg-bg pb-32 text-text">
      <DrinkPlayer
        steps={stepsOf(product).length > 0 ? stepsOf(product) : [{ title: t.loading, atSec: 0 }]}
        durationSec={product.video_duration_sec ?? 9}
        variant={brewVariantOf(product)}
        milkColor={milkColor}
        videoUrl={product.video_url || undefined}
        posterUrl={product.poster_url || undefined}
        title={product.name}
      />

      <div className="px-5 pt-3.5">
        <p className="text-xs text-accent-text">{product.slug}</p>
        <h1 className="mt-1 text-[30px] leading-tight font-normal tracking-tight">
          {product.name}
        </h1>
        <p className="mt-1 max-w-[320px] text-sm text-text-2">{product.description ?? ""}</p>

        <div className="mt-3 flex items-center gap-3">
          <PriceText kopeks={price} className="text-[30px]" />
          <span className="text-[13px] text-success">{t.bonusPlus(bonus)}</span>
          <div
            aria-hidden
            className="ml-auto w-16 transition-transform duration-500"
            style={{ transform: `scale(${sizeScale(product, selection)})` }}
          >
            <BrewView
              variant={brewVariantOf(product)}
              milkColor={milkColor}
              durationSec={product.video_duration_sec ?? 9}
            />
          </div>
        </div>

        {(product.groups ?? []).map((g) => {
          const chosen = selection[g.id] ?? [];
          const invalid = highlight.includes(g.id);
          const options = g.options ?? [];
          return (
            <div
              key={g.id}
              ref={(el) => {
                if (el) groupRefs.current.set(g.id, el);
              }}
              aria-invalid={invalid}
              className={`scroll-mt-24 rounded-tile ${invalid ? "ring-2 ring-[var(--danger)]" : ""}`}
            >
              <p className="mt-3.5 mb-2 text-[13px] text-text-2">
                {g.name}{" "}
                {g.min_select >= 1 ? (
                  <span className="text-accent-text">· {t.required}</span>
                ) : null}
              </p>
              {g.key === "size" && g.max_select === 1 ? (
                <SizeButtons
                  label={g.name}
                  value={String(chosen[0] ?? "")}
                  onChange={(v) => {
                    const opt = options.find((o) => String(o.id) === v);
                    if (opt) toggle(g.id, opt.id, 1);
                  }}
                  options={options.map((o) => ({
                    value: String(o.id),
                    label: o.name,
                    hint: o.available ? undefined : t.soldOut,
                  }))}
                />
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {options.map((o) => (
                    <span key={o.id} className={o.available ? "" : "opacity-40"}>
                      <Chip
                        pressed={chosen.includes(o.id)}
                        disabled={!o.available}
                        title={o.available ? undefined : t.unavailableOption}
                        onClick={() => toggle(g.id, o.id, g.max_select)}
                      >
                        {o.name}
                        {o.price_delta !== 0
                          ? ` ${o.price_delta > 0 ? "+" : "−"}${Math.abs(o.price_delta / 100)}`
                          : ""}
                      </Chip>
                    </span>
                  ))}
                </div>
              )}
              {invalid ? <p className="mt-1.5 text-xs text-danger">{t.chooseToContinue}</p> : null}
            </div>
          );
        })}
      </div>

      <div className="fixed inset-x-0 bottom-0 z-30 mx-auto w-full max-w-[480px] bg-[linear-gradient(transparent,var(--bg)_30%)] p-5 pb-[calc(var(--space-5)+var(--safe-bottom))]">
        <div className="[&>button]:w-full">
          <Button onClick={submit}>
            {t.addToOrder} · {formatRub(price)}
          </Button>
        </div>
      </div>
      <button
        type="button"
        onClick={() => nav(-1)}
        aria-label={t.back}
        className="fixed top-4 left-4 z-40 grid h-11 w-11 place-items-center rounded-full border border-[var(--line)] bg-[var(--glass-bg)] backdrop-blur-[var(--glass-blur)]"
      >
        ←
      </button>
      <Toast message={toast} />
    </main>
  );
}
