"""Ciclo de vida comum às fontes Python: descoberta multicast e envio UDP."""

import logging
import socket
import struct
import threading
from collections.abc import Callable

from google.protobuf.message import DecodeError

from common.config import multicast_group
from common.pb import pb

log = logging.getLogger(__name__)


class SourceRuntime:
    """Escuta o grupo multicast, aprende o endereço do Gateway e envia pacotes.

    Enquanto nenhuma descoberta chega, as leituras são descartadas: a fonte só
    conhece o Gateway pelo multicast; não há endereço configurado.
    """

    def __init__(self, describe: Callable[[], pb.SourceInfo]) -> None:
        self._describe = describe
        self._sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._gateway: tuple[str, int] | None = None
        self._lock = threading.Lock()

    @property
    def gateway(self) -> tuple[str, int] | None:
        with self._lock:
            return self._gateway

    def start(self) -> None:
        threading.Thread(target=self._listen_discovery, daemon=True).start()

    def send_reading(self, reading: pb.Reading) -> bool:
        return self._send(pb.UdpPacket(reading=reading))

    def announce(self) -> None:
        self._send(pb.UdpPacket(announcement=self._describe()))

    def _send(self, packet: pb.UdpPacket) -> bool:
        gateway = self.gateway
        if gateway is None:
            return False
        self._sender.sendto(packet.SerializeToString(), gateway)
        return True

    def _listen_discovery(self) -> None:
        sock = _open_multicast_listener(*multicast_group())
        while True:
            data, _ = sock.recvfrom(2048)
            request = pb.DiscoveryRequest()
            try:
                request.ParseFromString(data)
            except DecodeError as exc:
                log.debug("pacote multicast com Protobuf inválido: %s", exc)
                continue
            self._on_discovery((request.gateway_ip, request.gateway_udp_port))

    def _on_discovery(self, gateway: tuple[str, int]) -> None:
        with self._lock:
            changed = self._gateway != gateway
            self._gateway = gateway
        if changed:
            log.info("gateway descoberto em %s:%d", *gateway)
        self.announce()


def _open_multicast_listener(group: str, port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    # Várias fontes no mesmo host escutam a mesma porta multicast.
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.bind(("", port))
    membership = struct.pack("4s4s", socket.inet_aton(group), socket.inet_aton("0.0.0.0"))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
    return sock
