"""Sensor de umidade do solo (fonte orientada a eventos, não controlável).

Amostra o solo a cada segundo, envia leituras periódicas a cada INTERVAL_S e,
quando a umidade cruza o limiar de seca, envia um alerta imediatamente sem
esperar o próximo ciclo.
"""

import logging
import math
import random
import time
import zlib

from common.config import env, env_float, env_int, local_ip
from common.pb import pb
from common.source_runtime import SourceRuntime

SAMPLE_PERIOD_S = 1.0
CYCLE_S = 240.0  # período da oscilação simulada de umidade

log = logging.getLogger("soil")


class SoilSensor:
    def __init__(self) -> None:
        self.source_id = env("SOURCE_ID", "solo-a")
        self.field_id = env("FIELD_ID", "talhao-a")
        self.interval_s = env_int("INTERVAL_S", 5)
        self.dry_threshold = env_float("DRY_THRESHOLD", 25.0)
        # Fase derivada do id para que talhões diferentes sequem em momentos diferentes.
        self._phase = (zlib.crc32(self.source_id.encode()) % 360) * math.pi / 180
        self._start = time.monotonic()
        self._was_dry = False
        self.runtime = SourceRuntime(self.describe)

    def describe(self) -> pb.SourceInfo:
        return pb.SourceInfo(
            source_id=self.source_id,
            kind=pb.SOIL_SENSOR,
            field_id=self.field_id,
            ip=local_ip(),
            grpc_port=0,
            active=True,
            interval_s=self.interval_s,
            attributes={"dry_threshold_pct": f"{self.dry_threshold:.0f}"},
        )

    def run(self) -> None:
        self.runtime.start()
        log.info(
            "%s (%s) aguardando descoberta; limiar de seca %.0f%%", self.source_id, self.field_id, self.dry_threshold
        )
        last_periodic = 0.0
        while True:
            metrics = self._sample()
            self._check_event(metrics)
            now = time.monotonic()
            if now - last_periodic >= self.interval_s:
                self.runtime.send_reading(self._reading(metrics))
                last_periodic = now
            time.sleep(SAMPLE_PERIOD_S)

    def _sample(self) -> dict[str, float]:
        t = time.monotonic() - self._start
        angle = 2 * math.pi * t / CYCLE_S + self._phase
        moisture = 32 + 12 * math.sin(angle) + random.gauss(0, 0.8)
        soil_temp = 23 + 3 * math.cos(angle) + random.gauss(0, 0.3)
        return {"moisture_pct": round(max(0.0, moisture), 1), "soil_temp_c": round(soil_temp, 1)}

    def _check_event(self, metrics: dict[str, float]) -> None:
        """Dispara o alerta só na transição úmido -> seco, para não inundar o Gateway."""
        is_dry = metrics["moisture_pct"] < self.dry_threshold
        if is_dry and not self._was_dry:
            message = f"solo seco: {metrics['moisture_pct']:.1f}% < {self.dry_threshold:.0f}%"
            if self.runtime.send_reading(self._reading(metrics, alert=message)):
                log.warning("ALERTA enviado imediatamente: %s", message)
        self._was_dry = is_dry

    def _reading(self, metrics: dict[str, float], alert: str = "") -> pb.Reading:
        return pb.Reading(
            source_id=self.source_id,
            kind=pb.SOIL_SENSOR,
            field_id=self.field_id,
            timestamp_ms=int(time.time() * 1000),
            metrics=metrics,
            is_alert=bool(alert),
            alert_message=alert,
        )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    try:
        SoilSensor().run()
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
