"""Dashboard web em tempo real.

O navegador não fala Protobuf/TCP, então este processo é um cliente TCP do
Gateway (como o CLI) que traduz para HTTP: uma assinatura TCP alimenta um
fluxo Server-Sent Events, e comandos/consultas viram requisições TCP avulsas.
"""

import json
import logging
import mimetypes
import queue
import threading
import time
from collections import deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from common.config import env, env_int
from common.gateway_client import QUERY_KINDS, GatewayClient, GatewayError
from common.pb import pb

HISTORY_PER_SOURCE = 400  # ~10 min de leituras na frequência padrão
ALERT_HISTORY = 50
RECONNECT_DELAY_S = 2.0
# Build estático do frontend Next.js (web/out); configurável para o container.
WEB_ROOT = Path(env("WEB_ROOT", str(Path(__file__).resolve().parent.parent / "web" / "out"))).resolve()

log = logging.getLogger("dashboard")


def reading_to_dict(r: pb.Reading) -> dict[str, Any]:
    return {
        "source_id": r.source_id,
        "kind": pb.SourceKind.Name(r.kind),
        "field_id": r.field_id,
        "ts": r.timestamp_ms,
        "metrics": dict(r.metrics),
        "alert": r.is_alert,
        "alert_message": r.alert_message,
    }


def sources_to_list(sources: pb.SourceList) -> list[dict[str, Any]]:
    return [
        {
            "source_id": s.info.source_id,
            "kind": pb.SourceKind.Name(s.info.kind),
            "field_id": s.info.field_id,
            "address": f"{s.info.ip}:{s.info.grpc_port}" if s.info.grpc_port else s.info.ip,
            "controllable": s.info.grpc_port > 0,
            "active": s.info.active,
            "interval_s": s.info.interval_s,
            "attributes": dict(s.info.attributes),
            "online": s.online,
            "last_seen": s.last_seen_ms,
            "last_metrics": dict(s.last_metrics),
        }
        for s in sources.sources
    ]


class LiveState:
    """Estado em memória do dashboard e difusão para os navegadores conectados."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._connected = False
        self._sources: list[dict[str, Any]] = []
        self._history: dict[str, deque[dict[str, Any]]] = {}
        self._alerts: deque[dict[str, Any]] = deque(maxlen=ALERT_HISTORY)
        self._listeners: set[queue.Queue[str]] = set()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "connected": self._connected,
                "sources": self._sources,
                "history": {k: list(v) for k, v in self._history.items()},
                "alerts": list(self._alerts),
            }

    def add_listener(self) -> queue.Queue[str]:
        q: queue.Queue[str] = queue.Queue(maxsize=1000)
        with self._lock:
            self._listeners.add(q)
        return q

    def remove_listener(self, q: queue.Queue[str]) -> None:
        with self._lock:
            self._listeners.discard(q)

    def set_connected(self, connected: bool) -> None:
        with self._lock:
            changed = self._connected != connected
            self._connected = connected
        if changed:
            self._broadcast("status", {"connected": connected})

    def on_message(self, msg: pb.ServerMessage) -> None:
        body = msg.WhichOneof("body")
        if body == "reading":
            reading = reading_to_dict(msg.reading)
            with self._lock:
                self._history.setdefault(reading["source_id"], deque(maxlen=HISTORY_PER_SOURCE)).append(reading)
                if reading["alert"]:
                    self._alerts.append(reading)
            self._broadcast("reading", reading)
        elif body == "sources":
            sources = sources_to_list(msg.sources)
            with self._lock:
                self._sources = sources
            self._broadcast("sources", sources)

    def _broadcast(self, event: str, data: Any) -> None:
        frame = f"event: {event}\ndata: {json.dumps(data)}\n\n"
        with self._lock:
            listeners = list(self._listeners)
        for q in listeners:
            try:
                q.put_nowait(frame)
            except queue.Full:  # navegador travado: descarta em vez de bloquear o feed
                log.debug("fila SSE cheia; evento descartado")


def gateway_feed(state: LiveState) -> None:
    """Mantém uma assinatura TCP no Gateway, reconectando se ele cair."""
    while True:
        try:
            with GatewayClient() as client:
                log.info("assinatura TCP no gateway estabelecida")
                state.set_connected(True)
                for msg in client.subscribe():
                    state.on_message(msg)
        except OSError as exc:
            log.warning("gateway indisponível (%s); tentando de novo", exc)
        state.set_connected(False)
        time.sleep(RECONNECT_DELAY_S)


def resolve_static(path: str) -> Path | None:
    """Mapeia a URL para um arquivo do build, sem permitir sair de WEB_ROOT."""
    relative = path.lstrip("/") or "index.html"
    for candidate in (WEB_ROOT / relative, WEB_ROOT / f"{relative}.html", WEB_ROOT / relative / "index.html"):
        file = candidate.resolve()
        if file.is_file() and file.is_relative_to(WEB_ROOT):
            return file
    return None


def build_command(data: dict[str, Any]) -> pb.ValveCommand:
    command = pb.ValveCommand()
    if "open" in data:
        command.open = bool(data["open"])
    if "active" in data:
        command.active = bool(data["active"])
    if "flow_lpm" in data:
        command.flow_lpm = float(data["flow_lpm"])
    if "interval_s" in data:
        command.interval_s = int(data["interval_s"])
    return command


class Handler(BaseHTTPRequestHandler):
    state: LiveState

    def do_GET(self) -> None:
        url = urlparse(self.path)
        if url.path == "/events":
            self._stream_events()
        elif url.path == "/api/query":
            self._query(parse_qs(url.query))
        else:
            self._static(url.path)

    def _static(self, path: str) -> None:
        file = resolve_static(path)
        if file is None:
            self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain")
            return
        content_type = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
        self._send(HTTPStatus.OK, file.read_bytes(), content_type)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/command":
            self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain")
            return
        length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(length) or b"{}")
        try:
            with GatewayClient() as client:
                result = client.command(str(data.get("source_id", "")), build_command(data))
            self._json({"ok": result.ok, "message": result.message})
        except (OSError, GatewayError) as exc:
            self._json({"ok": False, "message": str(exc)})

    def _query(self, params: dict[str, list[str]]) -> None:
        kind = params.get("kind", ["driest"])[0]
        window = int(params.get("window", ["60"])[0])
        try:
            with GatewayClient() as client:
                result = client.query(QUERY_KINDS[kind], window)
            rows = [{"label": r.label, "values": dict(r.values)} for r in result.rows]
            self._json({"ok": True, "summary": result.summary, "rows": rows})
        except (OSError, GatewayError, KeyError) as exc:
            self._json({"ok": False, "summary": f"falha na consulta: {exc}", "rows": []})

    def _stream_events(self) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        q = self.state.add_listener()
        try:
            self.wfile.write(f"event: snapshot\ndata: {json.dumps(self.state.snapshot())}\n\n".encode())
            self.wfile.flush()
            while True:
                try:
                    frame = q.get(timeout=15)
                except queue.Empty:
                    frame = ": keep-alive\n\n"
                self.wfile.write(frame.encode())
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            log.debug("navegador encerrou a conexão SSE")
        finally:
            self.state.remove_listener(q)

    def _json(self, payload: Any) -> None:
        self._send(HTTPStatus.OK, json.dumps(payload).encode(), "application/json")

    def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        pass  # o SSE geraria uma linha de log por conexão longa


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    state = LiveState()
    threading.Thread(target=gateway_feed, args=(state,), daemon=True).start()
    Handler.state = state
    port = env_int("DASHBOARD_PORT", 8080)
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    server.daemon_threads = True
    log.info("dashboard em http://localhost:%d", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
