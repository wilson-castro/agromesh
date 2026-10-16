const numberFormats = new Map<number, Intl.NumberFormat>();

export function formatNumber(value: number, digits = 1): string {
  let format = numberFormats.get(digits);
  if (!format) {
    format = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: digits, maximumFractionDigits: digits });
    numberFormats.set(digits, format);
  }
  return format.format(value);
}

export function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString("pt-BR", { hour12: false });
}

export const KIND_LABEL = {
  SOIL_SENSOR: "Sensor de solo",
  WEATHER_STATION: "Estação meteorológica",
  IRRIGATION_VALVE: "Válvula · gRPC",
} as const;

export const METRIC_LABEL: Record<string, { label: string; unit: string }> = {
  moisture_pct: { label: "umidade", unit: "%" },
  soil_temp_c: { label: "solo", unit: "°C" },
  temperature_c: { label: "ar", unit: "°C" },
  air_humidity_pct: { label: "UR", unit: "%" },
  wind_kmh: { label: "vento", unit: " km/h" },
  rain_mm: { label: "chuva", unit: " mm" },
  flow_lpm: { label: "vazão", unit: " L/min" },
  liters_total: { label: "total", unit: " L" },
};

export function describeMetrics(metrics: Record<string, number>): string {
  const order = ["open", ...Object.keys(METRIC_LABEL)];
  const rank = (key: string) => (order.includes(key) ? order.indexOf(key) : order.length);
  return Object.entries(metrics)
    .sort(([a], [b]) => rank(a) - rank(b))
    .map(([key, value]) => {
      if (key === "open") return value ? "aberta" : "fechada";
      const meta = METRIC_LABEL[key] ?? { label: key, unit: "" };
      return `${meta.label} ${formatNumber(value)}${meta.unit}`;
    })
    .join(" · ");
}
