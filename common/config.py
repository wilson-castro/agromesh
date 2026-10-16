"""Configuração por variáveis de ambiente, com os mesmos nomes usados no gateway."""

import os
import socket


def env(key: str, default: str) -> str:
    return os.environ.get(key) or default


def env_int(key: str, default: int) -> int:
    try:
        return int(os.environ[key])
    except (KeyError, ValueError):
        return default


def env_float(key: str, default: float) -> float:
    try:
        return float(os.environ[key])
    except (KeyError, ValueError):
        return default


def multicast_group() -> tuple[str, int]:
    host, port = env("MCAST_ADDR", "239.255.10.1:9999").rsplit(":", 1)
    return host, int(port)


def gateway_tcp() -> tuple[str, int]:
    return env("GATEWAY_HOST", "127.0.0.1"), env_int("GATEWAY_TCP_PORT", 9200)


def local_ip() -> str:
    """IP pelo qual este host é alcançável (um connect UDP não envia pacotes)."""
    if advertised := os.environ.get("ADVERTISE_IP"):
        return advertised
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"
