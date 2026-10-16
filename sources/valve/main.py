"""Válvula de irrigação (fonte controlável).

Expõe o serviço gRPC `IrrigationValve` para o Gateway abrir/fechar, ajustar a
vazão, mudar a frequência de envio ou desativar a fonte (simulando falha), e
envia via UDP a vazão atual e o volume acumulado.
"""

import logging
import threading
import time
from concurrent import futures
from dataclasses import dataclass

import grpc

from common.config import env, env_float, env_int, local_ip
from common.pb import pb, pb_grpc
from common.source_runtime import SourceRuntime

TICK_S = 1.0

log = logging.getLogger("valve")


@dataclass
class ValveModel:
    source_id: str
    field_id: str
    active: bool = True
    open: bool = False
    flow_lpm: float = 20.0
    interval_s: int = 2
    liters_total: float = 0.0

    def to_proto(self) -> pb.ValveState:
        return pb.ValveState(
            source_id=self.source_id,
            field_id=self.field_id,
            active=self.active,
            open=self.open,
            flow_lpm=self.flow_lpm,
            interval_s=self.interval_s,
            liters_total=round(self.liters_total, 2),
        )

    def apply(self, cmd: pb.ValveCommand) -> None:
        # Campos `optional` no .proto: só altera o que o comando trouxe.
        if cmd.HasField("active"):
            self.active = cmd.active
        if cmd.HasField("open"):
            self.open = cmd.open
        if cmd.HasField("flow_lpm"):
            self.flow_lpm = max(0.0, cmd.flow_lpm)
        if cmd.HasField("interval_s") and cmd.interval_s > 0:
            self.interval_s = cmd.interval_s

    def current_flow(self) -> float:
        return self.flow_lpm if self.active and self.open else 0.0


class Valve(pb_grpc.IrrigationValveServicer):
    def __init__(self) -> None:
        self.model = ValveModel(
            source_id=env("SOURCE_ID", "valvula-a"),
            field_id=env("FIELD_ID", "talhao-a"),
            flow_lpm=env_float("FLOW_LPM", 20.0),
            interval_s=env_int("INTERVAL_S", 2),
        )
        self.lock = threading.Lock()
        self.grpc_port = 0
        self.runtime = SourceRuntime(self.describe)
        self._wake = threading.Event()

    # --- gRPC -------------------------------------------------------------
    def GetState(self, request: pb.ValveStateRequest, context: grpc.ServicerContext) -> pb.ValveState:
        with self.lock:
            return self.model.to_proto()

    def Configure(self, request: pb.ValveCommand, context: grpc.ServicerContext) -> pb.ValveState:
        with self.lock:
            self.model.apply(request)
            state = self.model.to_proto()
        log.info("comando recebido: %s -> %s", _compact(request), _compact(state))
        self._wake.set()  # telemetria imediata refletindo o novo estado
        return state

    # --- descoberta & telemetria -----------------------------------------
    def describe(self) -> pb.SourceInfo:
        with self.lock:
            m = self.model
            return pb.SourceInfo(
                source_id=m.source_id,
                kind=pb.IRRIGATION_VALVE,
                field_id=m.field_id,
                ip=local_ip(),
                grpc_port=self.grpc_port,
                active=m.active,
                interval_s=m.interval_s,
                attributes={"open": str(m.open).lower(), "flow_lpm": f"{m.flow_lpm:.1f}"},
            )

    def serve(self) -> None:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
        pb_grpc.add_IrrigationValveServicer_to_server(self, server)
        self.grpc_port = server.add_insecure_port(f"[::]:{env_int('GRPC_PORT', 0)}")
        server.start()
        self.runtime.start()
        log.info(
            "%s (%s) gRPC na porta %d; aguardando descoberta", self.model.source_id, self.model.field_id, self.grpc_port
        )
        self._telemetry_loop()

    def _telemetry_loop(self) -> None:
        last_sent = 0.0
        while True:
            woke = self._wake.wait(TICK_S)
            self._wake.clear()
            with self.lock:
                self.model.liters_total += self.model.current_flow() * TICK_S / 60
                active, interval = self.model.active, self.model.interval_s
                reading = self._reading()
            # Desativada = falha simulada: para de transmitir e o Gateway a marca offline.
            if active and (woke or time.monotonic() - last_sent >= interval):
                self.runtime.send_reading(reading)
                last_sent = time.monotonic()

    def _reading(self) -> pb.Reading:
        m = self.model
        return pb.Reading(
            source_id=m.source_id,
            kind=pb.IRRIGATION_VALVE,
            field_id=m.field_id,
            timestamp_ms=int(time.time() * 1000),
            metrics={
                "open": 1.0 if m.open else 0.0,
                "flow_lpm": m.current_flow(),
                "liters_total": round(m.liters_total, 2),
            },
        )


def _compact(msg: object) -> str:
    return str(msg).replace("\n", " ").strip()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    try:
        Valve().serve()
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
