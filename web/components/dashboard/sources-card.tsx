import { StatusDot } from "@/components/dashboard/status-dot";
import { ValveControls } from "@/components/dashboard/valve-controls";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { describeMetrics, KIND_LABEL } from "@/lib/format";
import type { Source } from "@/lib/types";
import { cn } from "@/lib/utils";

interface SourcesCardProps {
  sources: Source[];
  colors: Map<string, string>;
  now: number;
}

export function SourcesCard({ sources, colors, now }: SourcesCardProps) {
  return (
    <Card className="gap-3 py-4">
      <CardHeader className="px-4">
        <CardTitle className="text-sm">Fontes de dados</CardTitle>
        <CardDescription className="text-xs">Descobertas via multicast; válvulas controladas via gRPC</CardDescription>
      </CardHeader>
      <CardContent className="px-4">
        {sources.length === 0 ? (
          <p className="text-muted-foreground text-sm">Aguardando a descoberta multicast…</p>
        ) : (
          sources.map((source, i) => (
            <div key={source.source_id}>
              {i > 0 && <Separator className="my-3" />}
              <SourceRow source={source} color={colors.get(source.field_id)} now={now} />
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

function SourceRow({ source, color, now }: { source: Source; color?: string; now: number }) {
  const age = source.last_seen && now ? Math.max(0, Math.round((now - source.last_seen) / 1000)) : null;
  return (
    <div className={cn(!source.online && "opacity-60")}>
      <div className="flex items-center gap-2">
        <span
          aria-hidden
          className="size-2.5 shrink-0 rounded-[3px]"
          style={{ background: color ?? "var(--chart-5)" }}
        />
        <span className="font-medium">{source.source_id}</span>
        <span className="text-muted-foreground truncate text-xs">
          {KIND_LABEL[source.kind]} · {source.field_id}
        </span>
        <Badge variant="outline" className="ml-auto gap-1.5 font-normal">
          <StatusDot online={source.online} />
          {source.online ? "online" : "offline"}
        </Badge>
      </div>
      <p className="text-muted-foreground mt-1 text-xs tabular-nums">
        {describeMetrics(source.last_metrics) || "sem leituras"}
        {age !== null && ` — há ${age}s`}
      </p>
      {source.controllable && (
        // A chave remonta os campos quando o estado confirmado pela válvula muda.
        <ValveControls
          key={`${source.attributes.flow_lpm}-${source.interval_s}`}
          source={source}
        />
      )}
    </div>
  );
}
