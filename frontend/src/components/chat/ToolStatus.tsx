import { Loader2 } from "lucide-react";

import { cn } from "@/lib/utils";
import type { ToolStatusLabel } from "@/types/chat";

interface ToolStatusProps {
  status: ToolStatusLabel;
  className?: string;
}

export function ToolStatus({ status, className }: ToolStatusProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 rounded-full border border-border/70 bg-muted/60 px-3 py-1.5 text-xs text-muted-foreground",
        className
      )}
      role="status"
      aria-live="polite"
    >
      <Loader2 className="size-3.5 animate-spin" aria-hidden />
      <span>{status}</span>
    </div>
  );
}
