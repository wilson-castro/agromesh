// Formato JSON exposto pela ponte Python (dashboard/server.py).

export type SourceKind = "SOIL_SENSOR" | "WEATHER_STATION" | "IRRIGATION_VALVE";

export type Metrics = Record<string, number>;

export interface Source {
  source_id: string;
  kind: SourceKind;
  field_id: string;
  address: string;
  controllable: boolean;
  active: boolean;
  interval_s: number;
  attributes: Record<string, string>;
  online: boolean;
  last_seen: number;
  last_metrics: Metrics;
}

export interface Reading {
  source_id: string;
  kind: SourceKind;
  field_id: string;
  ts: number;
  metrics: Metrics;
  alert: boolean;
  alert_message: string;
}

export interface Snapshot {
  connected: boolean;
  sources: Source[];
  history: Record<string, Reading[]>;
  alerts: Reading[];
}

export type QueryKind = "driest" | "water" | "temp" | "alerts";

export interface QueryResult {
  ok: boolean;
  summary: string;
  rows: { label: string; values: Record<string, number> }[];
}

export interface ValveCommand {
  open?: boolean;
  active?: boolean;
  flow_lpm?: number;
  interval_s?: number;
}

export interface CommandResult {
  ok: boolean;
  message: string;
}
