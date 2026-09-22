import { ChatView } from "@/components/chat/ChatView";

function StatusIndicator() {
  return (
    <div className="inline-flex items-center gap-1.5 rounded-full border border-border/70 bg-muted/50 px-2.5 py-1 text-xs text-muted-foreground">
      <span className="relative flex size-2">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
        <span className="relative inline-flex size-2 rounded-full bg-emerald-500" />
      </span>
      Online
    </div>
  );
}

export default function Home() {
  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <header className="sticky top-0 z-20 border-b border-border/60 bg-background/90 backdrop-blur-md">
        <div className="mx-auto flex h-14 w-full max-w-2xl items-center justify-between px-3 sm:px-4">
          <div className="flex items-center gap-2.5">
            <div className="flex size-8 items-center justify-center rounded-lg bg-foreground text-xs font-semibold tracking-tight text-background">
              MA
            </div>
            <div>
              <h1 className="text-sm font-semibold tracking-tight">Market AI</h1>
              <p className="text-[11px] text-muted-foreground">
                Stocks & crypto assistant
              </p>
            </div>
          </div>
          <StatusIndicator />
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col min-h-0">
        <ChatView />
      </main>
    </div>
  );
}
