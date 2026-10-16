import { cn } from "@/lib/utils";

export function StatusDot({ online, className }: { online: boolean; className?: string }) {
  return (
    <span
      aria-hidden
      className={cn("inline-block size-2 shrink-0 rounded-full", online ? "bg-success" : "bg-destructive", className)}
    />
  );
}
