import type { ReactNode } from "react";

import { Card, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { formatNumber } from "@/lib/format";
import type { LiveState } from "@/lib/use-live-feed";

function Kpi({ label, value, unit, hint }: { label: string; value: ReactNode; unit?: string; hint: string }) {
  return (
    <Card className="gap-2 py-4">
      <CardHeader className="px-4">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-2xl font-semibold tabular-nums">
          {value}
          {unit && <span className="text-muted-foreground ml-1 text-base font-normal">{unit}</span>}
        </CardTitle>
      </CardHeader>
      <CardFooter className="text-muted-foreground truncate px-4 text-xs">{hint}</CardFooter>
    </Card>
  );
}

export function KpiCards({ state }: { state: LiveState }) {
  const { sources } = state;
  const online = sources.filter((s) => s.online);
  const offline = sources.filter((s) => !s.online).map((s) => s.source_id);

  const soil = online.filter((s) => s.kind === "SOIL_SENSOR" && "moisture_pct" in s.last_metrics);
  const avgMoisture = soil.length
    ? soil.reduce((sum, s) => sum + s.last_metrics.moisture_pct, 0) / soil.length
    : undefined;
  const driest = soil.reduce<(typeof soil)[number] | undefined>(
    (min, s) => (!min || s.last_metrics.moisture_pct < min.last_metrics.moisture_pct ? s : min),
    undefined,
  );

  const weather = sources.find((s) => s.kind === "WEATHER_STATION" && "temperature_c" in s.last_metrics)?.last_metrics;
  const valves = sources.filter((s) => s.kind === "IRRIGATION_VALVE");
  const liters = valves.reduce((sum, s) => sum + (s.last_metrics.liters_total ?? 0), 0);
  const openValves = valves.filter((s) => s.online && s.last_metrics.open === 1).length;

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
      <Kpi
        label="Fontes online"
        value={`${online.length}/${sources.length}`}
        hint={offline.length ? `offline: ${offline.join(", ")}` : "todas respondendo"}
      />
      <Kpi
        label="Umidade média do solo"
        value={avgMoisture === undefined ? "–" : formatNumber(avgMoisture)}
        unit="%"
        hint={driest ? `mais seco: ${driest.field_id} (${formatNumber(driest.last_metrics.moisture_pct)}%)` : "sem leituras"}
      />
      <Kpi
        label="Temperatura do ar"
        value={weather ? formatNumber(weather.temperature_c) : "–"}
        unit="°C"
        hint={
          weather
            ? `UR ${formatNumber(weather.air_humidity_pct, 0)}% · vento ${formatNumber(weather.wind_kmh, 0)} km/h`
            : "sem leituras"
        }
      />
      <Kpi
        label="Água aplicada"
        value={formatNumber(liters)}
        unit="L"
        hint={`${openValves} de ${valves.length} válvulas abertas`}
      />
      <Kpi label="Alertas de solo seco" value={state.alertCount} hint="desde que o painel abriu" />
    </div>
  );
}
