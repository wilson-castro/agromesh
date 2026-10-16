"""Cliente de linha de comando do AgroMesh (conecta ao Gateway via TCP).

Exemplos:
    python -m client.main list
    python -m client.main valve valvula-a --open --flow 35
    python -m client.main valve valvula-b --interval 5
    python -m client.main valve valvula-b --disable        # simula falha
    python -m client.main query driest --window 30
    python -m client.main watch
"""

import argparse
import sys
from datetime import datetime

from common.gateway_client import QUERY_KINDS, GatewayClient, GatewayError
from common.pb import pb

KIND_LABEL = {
    pb.SOIL_SENSOR: "sensor de solo",
    pb.WEATHER_STATION: "estação meteorológica",
    pb.IRRIGATION_VALVE: "válvula (gRPC)",
}


def cmd_list(client: GatewayClient, _: argparse.Namespace) -> None:
    sources = client.list_sources().sources
    if not sources:
        print("Nenhuma fonte descoberta ainda.")
        return
    print(f"{'FONTE':<14}{'TIPO':<24}{'TALHÃO':<11}{'STATUS':<9}{'ENDEREÇO':<22}ÚLTIMA LEITURA")
    for s in sources:
        info = s.info
        status = "online" if s.online else "OFFLINE"
        address = f"{info.ip}:{info.grpc_port}" if info.grpc_port else info.ip
        metrics = ", ".join(f"{k}={v:g}" for k, v in sorted(s.last_metrics.items()))
        print(
            f"{info.source_id:<14}{KIND_LABEL.get(info.kind, '?'):<24}"
            f"{info.field_id:<11}{status:<9}{address:<22}{metrics}"
        )


def cmd_valve(client: GatewayClient, args: argparse.Namespace) -> None:
    command = pb.ValveCommand()
    if args.open is not None:
        command.open = args.open
    if args.active is not None:
        command.active = args.active
    if args.flow is not None:
        command.flow_lpm = args.flow
    if args.interval is not None:
        command.interval_s = args.interval
    result = client.command(args.source_id, command)
    print(("OK: " if result.ok else "ERRO: ") + result.message)
    if result.ok:
        st = result.state
        print(
            f"  ativa={st.active} aberta={st.open} vazão={st.flow_lpm:g} L/min "
            f"intervalo={st.interval_s}s acumulado={st.liters_total:g} L"
        )


def cmd_query(client: GatewayClient, args: argparse.Namespace) -> None:
    result = client.query(QUERY_KINDS[args.kind], args.window)
    print(result.summary)
    for row in result.rows:
        values = "  ".join(f"{k}={v:.2f}" for k, v in sorted(row.values.items()))
        print(f"  {row.label:<14}{values}")


def cmd_watch(client: GatewayClient, _: argparse.Namespace) -> None:
    for msg in client.subscribe():
        if msg.WhichOneof("body") == "reading":
            r = msg.reading
            when = datetime.fromtimestamp(r.timestamp_ms / 1000).strftime("%H:%M:%S")
            metrics = ", ".join(f"{k}={v:g}" for k, v in sorted(r.metrics.items()))
            flag = f"  ⚠ {r.alert_message}" if r.is_alert else ""
            print(f"{when} {r.source_id:<12} {metrics}{flag}")
        elif msg.WhichOneof("body") == "sources":
            online = sum(s.online for s in msg.sources.sources)
            print(f"--- topologia: {online}/{len(msg.sources.sources)} fontes online")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agromesh", description="Cliente TCP do Gateway AgroMesh")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="lista fontes e estados").set_defaults(fn=cmd_list)

    valve = sub.add_parser("valve", help="envia comando a uma válvula (via Gateway -> gRPC)")
    valve.add_argument("source_id")
    valve.add_argument("--open", dest="open", action="store_true", default=None)
    valve.add_argument("--close", dest="open", action="store_false")
    valve.add_argument("--enable", dest="active", action="store_true", default=None)
    valve.add_argument("--disable", dest="active", action="store_false")
    valve.add_argument("--flow", type=float, help="vazão em L/min")
    valve.add_argument("--interval", type=int, help="intervalo de envio em segundos")
    valve.set_defaults(fn=cmd_valve)

    query = sub.add_parser("query", help="consulta analítica sobre o histórico")
    query.add_argument("kind", choices=sorted(QUERY_KINDS))
    query.add_argument("--window", type=int, default=60, help="janela em minutos (padrão 60)")
    query.set_defaults(fn=cmd_query)

    sub.add_parser("watch", help="acompanha leituras em tempo real").set_defaults(fn=cmd_watch)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        with GatewayClient() as client:
            args.fn(client, args)
    except OSError as exc:
        sys.exit(f"Gateway indisponível: {exc}")
    except GatewayError as exc:
        sys.exit(f"Erro do gateway: {exc}")
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
