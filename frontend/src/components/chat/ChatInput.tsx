"use client";

import { ArrowUp } from "lucide-react";
import { useEffect, useRef, type FormEvent, type KeyboardEvent } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  isLoading?: boolean;
  placeholder?: string;
  className?: string;
}

export function ChatInput({
  value,
  onChange,
  onSubmit,
  isLoading = false,
  placeholder = "Ask about stocks or crypto…",
  className,
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "0px";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [value]);

  function handleSubmit(event?: FormEvent) {
    event?.preventDefault();
    if (!value.trim() || isLoading) return;
    onSubmit();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={cn(
        "sticky bottom-0 z-10 border-t border-border/60 bg-background/90 px-3 py-3 backdrop-blur-md sm:px-4",
        className
      )}
    >
      <div className="mx-auto flex w-full max-w-2xl items-end gap-2 rounded-2xl border border-border bg-card p-2 shadow-sm">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          placeholder={placeholder}
          disabled={isLoading}
          aria-label="Chat message"
          className="max-h-40 min-h-10 flex-1 resize-none bg-transparent px-2 py-2 text-sm leading-relaxed outline-none placeholder:text-muted-foreground disabled:opacity-60"
        />
        <Button
          type="submit"
          size="icon"
          disabled={!value.trim() || isLoading}
          aria-label={isLoading ? "Sending" : "Send message"}
          className="shrink-0 rounded-xl"
        >
          <ArrowUp className="size-4" />
        </Button>
      </div>
      <p className="mx-auto mt-2 max-w-2xl text-center text-[11px] text-muted-foreground">
        Mock responses for now. Enter to send, Shift+Enter for a new line.
      </p>
    </form>
  );
}
