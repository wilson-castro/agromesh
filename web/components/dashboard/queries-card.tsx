"use client";

import { Database, Loader2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { runQuery } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import type { QueryKind, QueryResult } from "@/lib/types";

const QUERIES: { kind: QueryKind; label: string; entity: string }[] = [
  { kind: "driest", label: "Talhão mais seco", entity: "Talhão" },
  { kind: "water", label: "Consumo de água", entity: "Talhão" },
  { kind: "temp", label: "Temperatura: média e desvio", entity: "Estação" },
  { kind: "alerts", label: "Alertas por talhão", entity: "Talhão" },
];

const WINDOWS = [
  { value: "5", label: "Últimos 5 min" },
  { value: "15", label: "Últimos 15 min" },
  { value: "60", label: "Última hora" },
  { value: "1440", label: "Últimas 24 h" },
];

const COLUMN_LABEL: Record<string, string> = {
  umidade_media_pct: "Umidade média (%)",
  umidade_min_pct: "Umidade mín. (%)",
  amostras: "Amostras",
  litros: "Litros",
  media_c: "Média (°C)",
  desvio_padrao_c: "Desvio padrão (°C)",
  min_c: "Mín. (°C)",
  max_c: "Máx. (°C)",
  alertas: "Alertas",
};

const INTEGER_COLUMNS = new Set(["amostras", "alertas"]);

export function QueriesCard() {
  const [windowMinutes, setWindowMinutes] = useState("60");
  const [active, setActive] = useState<(typeof QUERIES)[number] | null>(null);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);

  async function execute(query: (typeof QUERIES)[number]) {
    setActive(query);
    setLoading(true);
    setResult(await runQuery(query.kind, Number(windowMinutes)));
    setLoading(false);
  }

  const columns = result?.rows[0] ? Object.keys(result.rows[0].values) : [];

  return (
    <Card className="gap-3 py-4">
      <CardHeader className="px-4">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Database className="size-4" />
          Consultas analíticas
        </CardTitle>
        <CardDescription className="text-xs">Agregações sobre o histórico SQLite do gateway</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 px-4">
        <div className="flex flex-wrap items-center gap-2">
          <Select value={windowMinutes} onValueChange={setWindowMinutes}>
            <SelectTrigger size="sm" className="w-40" aria-label="Janela de tempo">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {WINDOWS.map((w) => (
                <SelectItem key={w.value} value={w.value}>
                  {w.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {QUERIES.map((query) => (
            <Button
              key={query.kind}
              size="sm"
              variant={active?.kind === query.kind ? "default" : "outline"}
              disabled={loading}
              onClick={() => execute(query)}
            >
              {query.label}
            </Button>
          ))}
        </div>

        {loading && (
          <p className="text-muted-foreground flex items-center gap-2 text-sm">
            <Loader2 className="size-4 animate-spin" /> Consultando o gateway…
          </p>
        )}
        {!loading && !result && <p className="text-muted-foreground text-sm">Escolha uma consulta.</p>}
        {!loading && result && (
          <div className="space-y-3">
            <p className="text-sm font-medium">{result.summary}</p>
            {result.rows.length > 0 && (
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{active?.entity}</TableHead>
                      {columns.map((c) => (
                        <TableHead key={c} className="text-right">
                          {COLUMN_LABEL[c] ?? c}
                        </TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.rows.map((row) => (
                      <TableRow key={row.label}>
                        <TableCell className="font-medium">{row.label}</TableCell>
                        {columns.map((c) => (
                          <TableCell key={c} className="text-right font-mono tabular-nums">
                            {formatNumber(row.values[c] ?? 0, INTEGER_COLUMNS.has(c) ? 0 : 2)}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
