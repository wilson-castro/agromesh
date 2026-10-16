"""Cliente TCP do Gateway, usado pelo CLI e pelo dashboard."""

import itertools
import socket
from collections.abc import Iterator
from typing import Self

from common.config import gateway_tcp
from common.framing import recv_message, send_message
from common.pb import pb

QUERY_KINDS: dict[str, int] = {
    "driest": pb.DRIEST_FIELD,
    "water": pb.WATER_USAGE,
    "temp": pb.TEMPERATURE_STATS,
    "alerts": pb.ALERTS_PER_FIELD,
}


class GatewayError(RuntimeError):
    pass


class GatewayClient:
    """Uma conexão TCP com requisições numeradas (request_id) e respostas em ordem."""

    def __init__(self, address: tuple[str, int] | None = None, timeout: float = 5.0) -> None:
        self._sock = socket.create_connection(address or gateway_tcp(), timeout=timeout)
        self._ids = itertools.count(1)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._sock.close()

    def list_sources(self) -> pb.SourceList:
        return self._call(pb.ClientRequest(list_sources=pb.ListSourcesRequest())).sources

    def command(self, source_id: str, command: pb.ValveCommand) -> pb.CommandResult:
        request = pb.ClientRequest(command=pb.CommandRequest(source_id=source_id, command=command))
        return self._call(request).command_result

    def query(self, kind: int, window_minutes: int) -> pb.QueryResult:
        request = pb.ClientRequest(query=pb.QueryRequest(kind=kind, window_minutes=window_minutes))  # type: ignore[arg-type]
        return self._call(request).query_result

    def subscribe(self) -> Iterator[pb.ServerMessage]:
        """Assina leituras e topologia; o iterador termina se a conexão cair."""
        self._sock.settimeout(None)
        send_message(self._sock, pb.ClientRequest(request_id=next(self._ids), subscribe=pb.SubscribeRequest()))
        while True:
            yield recv_message(self._sock, pb.ServerMessage())

    def _call(self, request: pb.ClientRequest) -> pb.ServerMessage:
        request.request_id = next(self._ids)
        send_message(self._sock, request)
        response = recv_message(self._sock, pb.ServerMessage())
        if response.WhichOneof("body") == "error":
            raise GatewayError(response.error)
        return response
