import { cn } from "@/lib/utils";
import type { StockQuote } from "@/types/chat";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface MarketCardProps {
  data: StockQuote;
  className?: string;
}

function formatPrice(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: value >= 1000 ? 2 : 4,
  }).format(value);
}

function formatVolume(value: number) {
  return new Intl.NumberFormat("en-US", {
    notation: value >= 1_000_000 ? "compact" : "standard",
    maximumFractionDigits: 2,
  }).format(value);
}

function formatTimestamp(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function MarketCard({ data, className }: MarketCardProps) {
  return (
    <Card
      size="sm"
      className={cn(
        "w-full max-w-sm border-border/80 bg-card shadow-none",
        className
      )}
    >
      <CardHeader className="pb-0">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="font-semibold tracking-tight">
            {data.symbol}
          </CardTitle>
          <span className="rounded-md bg-muted px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
            stock
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 pt-1">
        <div>
          <p className="text-xl font-semibold tabular-nums tracking-tight">
            {formatPrice(data.close)}
          </p>
          <p className="text-xs text-muted-foreground">
            Close · {formatTimestamp(data.timestamp)}
          </p>
        </div>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs sm:grid-cols-4">
          <div>
            <dt className="text-muted-foreground">Open</dt>
            <dd className="font-medium tabular-nums">
              {formatPrice(data.open)}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">High</dt>
            <dd className="font-medium tabular-nums">
              {formatPrice(data.high)}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Low</dt>
            <dd className="font-medium tabular-nums">
              {formatPrice(data.low)}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Volume</dt>
            <dd className="font-medium tabular-nums">
              {formatVolume(data.volume)}
            </dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}
