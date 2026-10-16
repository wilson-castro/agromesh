"use client";

import { Power, PowerOff, Send, Waves, X } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { sendCommand } from "@/lib/api";
import type { Source, ValveCommand } from "@/lib/types";

export function ValveControls({ source }: { source: Source }) {
  const isOpen = source.attributes.open === "true";
  const [flow, setFlow] = useState(source.attributes.flow_lpm ?? "20");
  const [intervalS, setIntervalS] = useState(String(source.interval_s));
  const [pending, setPending] = useState(false);

  async function run(command: ValveCommand) {
    setPending(true);
    const result = await sendCommand(source.source_id, command);
    setPending(false);
    if (result.ok) toast.success(`${source.source_id}: ${result.message}`);
    else toast.error(`${source.source_id}: ${result.message}`);
  }

  return (
    <div className="mt-3 space-y-3">
      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant="outline" disabled={pending} onClick={() => run({ open: !isOpen })}>
          {isOpen ? <X /> : <Waves />}
          {isOpen ? "Fechar válvula" : "Abrir válvula"}
        </Button>
        <Button
          size="sm"
          variant={source.active ? "ghost" : "secondary"}
          disabled={pending}
          onClick={() => run({ active: !source.active })}
        >
          {source.active ? <PowerOff /> : <Power />}
          {source.active ? "Simular falha" : "Reativar"}
        </Button>
      </div>
      <form
        className="flex flex-wrap items-end gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          void run({ flow_lpm: Number(flow), interval_s: Number(intervalS) });
        }}
      >
        <div className="grid gap-1">
          <Label htmlFor={`${source.source_id}-flow`} className="text-muted-foreground text-xs">
            Vazão (L/min)
          </Label>
          <Input
            id={`${source.source_id}-flow`}
            type="number"
            min={0}
            className="h-8 w-24"
            value={flow}
            onChange={(e) => setFlow(e.target.value)}
          />
        </div>
        <div className="grid gap-1">
          <Label htmlFor={`${source.source_id}-interval`} className="text-muted-foreground text-xs">
            Envio (s)
          </Label>
          <Input
            id={`${source.source_id}-interval`}
            type="number"
            min={1}
            className="h-8 w-20"
            value={intervalS}
            onChange={(e) => setIntervalS(e.target.value)}
          />
        </div>
        <Button size="sm" type="submit" disabled={pending}>
          <Send />
          Aplicar
        </Button>
      </form>
    </div>
  );
}
