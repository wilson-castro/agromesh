"use client";

import { CartesianGrid, Line, LineChart, ReferenceLine, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  type ChartConfig,
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { formatNumber, formatTime } from "@/lib/format";
import { type ChartRow, WINDOW_MS } from "@/lib/series";

interface LiveChartProps {
  title: string;
  description: string;
  unit: string;
  data: ChartRow[];
  config: ChartConfig;
  keys: string[];
  now: number;
  step?: boolean;
  domain?: [number | "auto", number | "auto" | ((dataMax: number) => number)];
  threshold?: { value: number; label: string };
}

const MINUTE_TICKS = [5, 4, 3, 2, 1, 0];

export function LiveChart({ title, description, unit, data, config, keys, now, step, domain, threshold }: LiveChartProps) {
  const ticks = MINUTE_TICKS.map((m) => now - m * 60_000);

  return (
    <Card className="gap-3 py-4">
      <CardHeader className="px-4">
        <CardTitle className="text-sm">{title}</CardTitle>
        <CardDescription className="text-xs">{description}</CardDescription>
      </CardHeader>
      <CardContent className="px-2 sm:px-4">
        {data.length === 0 ? (
          <div className="text-muted-foreground flex h-48 items-center justify-center text-sm">
            Aguardando leituras…
          </div>
        ) : (
          <ChartContainer config={config} className="aspect-auto h-48 w-full">
            <LineChart data={data} margin={{ left: 0, right: 8, top: 8 }}>
              <CartesianGrid vertical={false} />
              <XAxis
                dataKey="t"
                type="number"
                domain={[now - WINDOW_MS, now]}
                ticks={ticks}
                tickFormatter={(t: number) => (t >= now - 1000 ? "agora" : `-${Math.round((now - t) / 60_000)} min`)}
                tickLine={false}
                axisLine={false}
                allowDataOverflow
              />
              <YAxis
                width={36}
                domain={domain ?? ["auto", "auto"]}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v: number) => formatNumber(v, 0)}
              />
              {threshold && (
                <ReferenceLine
                  y={threshold.value}
                  stroke="var(--destructive)"
                  strokeDasharray="4 4"
                  label={{ value: threshold.label, position: "insideTopLeft", fill: "var(--destructive)", fontSize: 11 }}
                />
              )}
              <ChartTooltip
                content={
                  <ChartTooltipContent
                    labelFormatter={(_, payload) => formatTime(Number(payload?.[0]?.payload?.t ?? 0))}
                    formatter={(value, name, item) => (
                      <div className="flex w-full items-center gap-2">
                        <span className="size-2.5 shrink-0 rounded-[2px]" style={{ background: item.color }} />
                        <span className="text-muted-foreground">{config[String(name)]?.label ?? name}</span>
                        <span className="ml-auto font-mono font-medium tabular-nums">
                          {formatNumber(Number(value))}
                          {unit}
                        </span>
                      </div>
                    )}
                  />
                }
              />
              {keys.length > 1 && <ChartLegend content={<ChartLegendContent />} />}
              {keys.map((key) => (
                <Line
                  key={key}
                  dataKey={key}
                  type={step ? "stepAfter" : "monotone"}
                  stroke={`var(--color-${key})`}
                  strokeWidth={2}
                  dot={false}
                  connectNulls
                  isAnimationActive={false}
                />
              ))}
            </LineChart>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  );
}
