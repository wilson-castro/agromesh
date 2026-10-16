import { TriangleAlert } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { formatTime } from "@/lib/format";
import type { Reading } from "@/lib/types";
import { cn } from "@/lib/utils";

const FRESH_MS = 30_000;

export function AlertsCard({ alerts, now }: { alerts: Reading[]; now: number }) {
  return (
    <Card className="gap-3 py-4">
      <CardHeader className="px-4">
        <CardTitle className="text-sm">Alertas em tempo real</CardTitle>
        <CardDescription className="text-xs">Enviados pelo sensor no instante em que o solo cruza o limiar</CardDescription>
      </CardHeader>
      <CardContent className="px-4">
        {alerts.length === 0 ? (
          <p className="text-muted-foreground text-sm">Nenhum alerta ainda.</p>
        ) : (
          <ScrollArea className="h-56 pr-3">
            <ul className="space-y-1.5">
              {alerts.map((alert) => (
                <li
                  key={`${alert.source_id}-${alert.ts}`}
                  className={cn(
                    "flex items-start gap-2 rounded-md px-2 py-1.5 text-xs",
                    now - alert.ts < FRESH_MS && "bg-destructive/10",
                  )}
                >
                  <TriangleAlert className="text-destructive mt-px size-3.5 shrink-0" aria-label="alerta" />
                  <span className="text-muted-foreground font-mono tabular-nums">{formatTime(alert.ts)}</span>
                  <span>
                    <span className="font-medium">{alert.field_id}</span> · {alert.alert_message}
                  </span>
                </li>
              ))}
            </ul>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
