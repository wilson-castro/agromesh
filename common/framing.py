"""Framing TCP: 4 bytes big-endian com o tamanho, seguidos do payload Protobuf."""

import socket
import struct

from google.protobuf.message import Message

_HEADER = struct.Struct(">I")
MAX_FRAME_SIZE = 4 << 20


def send_message(sock: socket.socket, msg: Message) -> None:
    payload = msg.SerializeToString()
    sock.sendall(_HEADER.pack(len(payload)) + payload)


def recv_message[M: Message](sock: socket.socket, msg: M) -> M:
    (size,) = _HEADER.unpack(_recv_exact(sock, _HEADER.size))
    if size > MAX_FRAME_SIZE:
        raise ValueError(f"frame grande demais: {size} bytes")
    msg.ParseFromString(_recv_exact(sock, size))
    return msg


def _recv_exact(sock: socket.socket, size: int) -> bytes:
    """recv pode devolver menos bytes que o pedido; acumula até completar."""
    chunks = bytearray()
    while len(chunks) < size:
        chunk = sock.recv(size - len(chunks))
        if not chunk:
            raise ConnectionError("conexão encerrada pelo gateway")
        chunks.extend(chunk)
    return bytes(chunks)
