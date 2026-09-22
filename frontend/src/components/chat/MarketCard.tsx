import { TrendingDown, TrendingUp } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { MarketQuote } from "@/types/chat";

interface MarketCardProps {
  data: MarketQuote;
  className?: string;
}

function formatPrice(price: number, currency: string) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: price >= 1000 ? 2 : 4,
  }).format(price);
}

export function MarketCard({ data, className }: MarketCardProps) {
  const isUp = data.change24h >= 0;

  return (
    <Card
      size="sm"
      className={cn(
        "w-full max-w-xs border-border/80 bg-card shadow-none",
        className
      )}
    >
      <CardHeader className="pb-0">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="font-semibold tracking-tight">
            {data.symbol}
          </CardTitle>
          <span className="rounded-md bg-muted px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
            {data.assetType}
          </span>
        </div>
      </CardHeader>
      <CardContent className="flex items-end justify-between gap-3 pt-1">
        <div>
          <p className="text-xl font-semibold tabular-nums tracking-tight">
            {formatPrice(data.price, data.currency)}
          </p>
          <p className="text-xs text-muted-foreground">{data.currency}</p>
        </div>
        <div
          className={cn(
            "inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium tabular-nums",
            isUp
              ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400"
              : "bg-rose-500/10 text-rose-700 dark:text-rose-400"
          )}
        >
          {isUp ? (
            <TrendingUp className="size-3.5" aria-hidden />
          ) : (
            <TrendingDown className="size-3.5" aria-hidden />
          )}
          {isUp ? "+" : ""}
          {data.change24h.toFixed(2)}%
        </div>
      </CardContent>
    </Card>
  );
}
