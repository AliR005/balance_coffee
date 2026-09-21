import { formatRub } from "../lib/format";

interface Props {
  kopeks: number;
  className?: string;
}

/** Крупная цена: tabular, Intl.NumberFormat. Деньги — int копеек. */
export function PriceText({ kopeks, className = "" }: Props) {
  return (
    <b data-testid="price" className={`tabular font-semibold ${className}`}>
      {formatRub(kopeks)}
    </b>
  );
}
