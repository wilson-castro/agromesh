import socket

from common.framing import recv_message, send_message
from common.pb import pb


def test_frame_roundtrip_over_socketpair() -> None:
    a, b = socket.socketpair()
    with a, b:
        sent = pb.ClientRequest(request_id=7, query=pb.QueryRequest(kind=pb.WATER_USAGE, window_minutes=30))
        send_message(a, sent)
        send_message(a, pb.ClientRequest(request_id=8))
        assert recv_message(b, pb.ClientRequest()) == sent
        assert recv_message(b, pb.ClientRequest()).request_id == 8
