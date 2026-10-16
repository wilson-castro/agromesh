import { Sprout } from "lucide-react";

import { StatusDot } from "@/components/dashboard/status-dot";
import { Badge } from "@/components/ui/badge";
import { formatTime } from "@/lib/format";

export function SiteHeader({ connected, now }: { connected: boolean; now: number }) {
  return (
    <header className="bg-card sticky top-0 z-10 border-b">
      <div className="mx-auto flex h-14 max-w-screen-2xl items-center gap-3 px-4 sm:px-6">
        <div className="bg-primary text-primary-foreground flex size-8 items-center justify-center rounded-md">
          <Sprout className="size-4" />
        </div>
        <div className="flex min-w-0 flex-col leading-tight">
          <span className="font-semibold">AgroMesh</span>
          <span className="text-muted-foreground truncate text-xs">Central da fazenda · irrigação por talhão</span>
        </div>
        <div className="ml-auto flex items-center gap-3">
          <Badge variant="outline" className="gap-1.5 font-normal">
            <StatusDot online={connected} />
            {connected ? "Gateway conectado" : "Gateway desconectado"}
          </Badge>
          <span className="text-muted-foreground hidden font-mono text-sm tabular-nums sm:inline">
            {now ? formatTime(now) : "--:--:--"}
          </span>
        </div>
      </div>
    </header>
  );
}
