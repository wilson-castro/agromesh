import type { CommandResult, QueryKind, QueryResult, ValveCommand } from "@/lib/types";

export async function sendCommand(sourceId: string, command: ValveCommand): Promise<CommandResult> {
  try {
    const res = await fetch("/api/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source_id: sourceId, ...command }),
    });
    return (await res.json()) as CommandResult;
  } catch {
    return { ok: false, message: "dashboard indisponível" };
  }
}

export async function runQuery(kind: QueryKind, windowMinutes: number): Promise<QueryResult> {
  try {
    const res = await fetch(`/api/query?kind=${kind}&window=${windowMinutes}`);
    return (await res.json()) as QueryResult;
  } catch {
    return { ok: false, summary: "dashboard indisponível", rows: [] };
  }
}
