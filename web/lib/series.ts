import type { ChartConfig } from "@/components/ui/chart";
import type { Reading, Source, SourceKind } from "@/lib/types";

export const WINDOW_MS = 5 * 60 * 1000;
const BUCKET_MS = 5000;
const FIELD_COLORS = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)"];

export type ChartRow = { t: number } & Record<string, number>;

// A cor segue o talhão (ordem alfabética, estável), nunca a posição no gráfico:
// o mesmo talhão tem a mesma cor em todos os painéis.
export function fieldColors(sources: Source[]): Map<string, string> {
  const fields = [...new Set(sources.filter((s) => s.kind !== "WEATHER_STATION").map((s) => s.field_id))].sort();
  return new Map(fields.map((field, i) => [field, FIELD_COLORS[Math.min(i, FIELD_COLORS.length - 1)]]));
}

interface SeriesSpec {
  sources: Source[];
  history: Record<string, Reading[]>;
  kind: SourceKind;
  metric: string;
  now: number;
  colors: Map<string, string>;
  fallbackColor?: string;
}

// Agrupa as leituras em baldes de 5 s para alinhar fontes com intervalos diferentes
// em uma única linha do tempo, o que deixa o tooltip mostrar todos os talhões juntos.
export function buildSeries({ sources, history, kind, metric, now, colors, fallbackColor }: SeriesSpec) {
  const start = now - WINDOW_MS;
  const ofKind = sources.filter((s) => s.kind === kind);
  const config: ChartConfig = {};
  const buckets = new Map<number, ChartRow>();

  for (const source of ofKind) {
    const key = source.field_id;
    config[key] = { label: key, color: colors.get(key) ?? fallbackColor ?? "var(--chart-1)" };
    for (const reading of history[source.source_id] ?? []) {
      const value = reading.metrics[metric];
      if (reading.ts < start || value === undefined) continue;
      const t = Math.floor(reading.ts / BUCKET_MS) * BUCKET_MS;
      const row = buckets.get(t) ?? ({ t } as ChartRow);
      row[key] = value;
      buckets.set(t, row);
    }
  }
  const data = [...buckets.values()].sort((a, b) => a.t - b.t);
  return { data, config, keys: Object.keys(config) };
}
