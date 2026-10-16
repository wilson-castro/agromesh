"use client";

import { useEffect, useReducer, useState } from "react";

import type { Reading, Snapshot, Source } from "@/lib/types";

const HISTORY_MS = 10 * 60 * 1000;
const MAX_ALERTS = 50;

export interface LiveState {
  connected: boolean;
  sources: Source[];
  history: Record<string, Reading[]>;
  alerts: Reading[];
  alertCount: number;
}

type Action =
  | { type: "snapshot"; snapshot: Snapshot }
  | { type: "reading"; reading: Reading }
  | { type: "sources"; sources: Source[] }
  | { type: "status"; connected: boolean };

const initialState: LiveState = { connected: false, sources: [], history: {}, alerts: [], alertCount: 0 };

function reducer(state: LiveState, action: Action): LiveState {
  switch (action.type) {
    case "snapshot":
      return {
        connected: action.snapshot.connected,
        sources: action.snapshot.sources,
        history: action.snapshot.history,
        alerts: [...action.snapshot.alerts].reverse(),
        alertCount: action.snapshot.alerts.length,
      };
    case "reading":
      return applyReading(state, action.reading);
    case "sources":
      return { ...state, sources: action.sources };
    case "status":
      return { ...state, connected: action.connected };
  }
}

function applyReading(state: LiveState, reading: Reading): LiveState {
  const cutoff = reading.ts - HISTORY_MS;
  const previous = state.history[reading.source_id] ?? [];
  const history = { ...state.history, [reading.source_id]: [...previous.filter((r) => r.ts >= cutoff), reading] };
  const sources = state.sources.map((s) =>
    s.source_id === reading.source_id ? { ...s, last_metrics: reading.metrics, last_seen: reading.ts } : s,
  );
  if (!reading.alert) return { ...state, history, sources };
  return {
    ...state,
    history,
    sources,
    alerts: [reading, ...state.alerts].slice(0, MAX_ALERTS),
    alertCount: state.alertCount + 1,
  };
}

// Assina o fluxo SSE da ponte; o EventSource reconecta sozinho se ela cair.
export function useLiveFeed(): LiveState {
  const [state, dispatch] = useReducer(reducer, initialState);

  useEffect(() => {
    const source = new EventSource("/events");
    const on = <T,>(event: string, handle: (data: T) => void) =>
      source.addEventListener(event, (e) => handle(JSON.parse((e as MessageEvent<string>).data) as T));

    on<Snapshot>("snapshot", (snapshot) => dispatch({ type: "snapshot", snapshot }));
    on<Reading>("reading", (reading) => dispatch({ type: "reading", reading }));
    on<Source[]>("sources", (sources) => dispatch({ type: "sources", sources }));
    on<{ connected: boolean }>("status", ({ connected }) => dispatch({ type: "status", connected }));
    source.onerror = () => dispatch({ type: "status", connected: false });
    return () => source.close();
  }, []);

  return state;
}

// Relógio compartilhado para janelas de tempo e "há Xs" avançarem sem novas leituras.
export function useNow(intervalMs = 1000): number {
  const [now, setNow] = useState(0);
  useEffect(() => {
    const tick = () => setNow(Date.now());
    tick();
    const id = setInterval(tick, intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);
  return now;
}
