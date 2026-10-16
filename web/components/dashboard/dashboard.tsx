"use client";

import { useMemo } from "react";

import { AlertsCard } from "@/components/dashboard/alerts-card";
import { KpiCards } from "@/components/dashboard/kpi-cards";
import { LiveChart } from "@/components/dashboard/live-chart";
import { QueriesCard } from "@/components/dashboard/queries-card";
import { SiteHeader } from "@/components/dashboard/site-header";
import { SourcesCard } from "@/components/dashboard/sources-card";
import { buildSeries, fieldColors } from "@/lib/series";
import { useLiveFeed, useNow } from "@/lib/use-live-feed";

const DRY_THRESHOLD = 25;

export function Dashboard() {
  const state = useLiveFeed();
  const now = useNow();
  const colors = useMemo(() => fieldColors(state.sources), [state.sources]);
  const common = { sources: state.sources, history: state.history, now, colors };

  const moisture = buildSeries({ ...common, kind: "SOIL_SENSOR", metric: "moisture_pct" });
  const flow = buildSeries({ ...common, kind: "IRRIGATION_VALVE", metric: "flow_lpm" });
  const temperature = buildSeries({
    ...common,
    kind: "WEATHER_STATION",
    metric: "temperature_c",
    fallbackColor: "var(--chart-5)",
  });

  return (
    <div className="min-h-svh">
      <SiteHeader connected={state.connected} now={now} />
      <main className="mx-auto grid max-w-screen-2xl gap-4 p-4 sm:p-6">
        <KpiCards state={state} />
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="grid gap-4 lg:col-span-2">
            <LiveChart
              title="Umidade do solo"
              description="Por talhão, últimos 5 minutos (%)"
              unit="%"
              domain={[0, 60]}
              threshold={{ value: DRY_THRESHOLD, label: `limiar de seca ${DRY_THRESHOLD}%` }}
              now={now}
              {...moisture}
            />
            <LiveChart
              title="Vazão das válvulas"
              description="Por talhão, últimos 5 minutos (L/min)"
              unit=" L/min"
              domain={[0, (max) => Math.ceil((max + 1) / 10) * 10]}
              step
              now={now}
              {...flow}
            />
            <LiveChart
              title="Temperatura do ar"
              description="Estação meteorológica, últimos 5 minutos (°C)"
              unit=" °C"
              now={now}
              {...temperature}
            />
          </div>
          <div className="grid content-start gap-4">
            <SourcesCard sources={state.sources} colors={colors} now={now} />
            <AlertsCard alerts={state.alerts} now={now} />
          </div>
        </div>
        <QueriesCard />
      </main>
    </div>
  );
}
