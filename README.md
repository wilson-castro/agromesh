# AgroMesh

Monitoramento e irrigação de uma fazenda dividida em talhões. Sensores e válvulas são
processos independentes que o gateway encontra por multicast, recebem comandos via gRPC e
enviam telemetria por UDP. Um painel web mostra tudo em tempo real.

- **Gateway** (Go): descoberta, ingestão, histórico em SQLite, consultas e proxy gRPC.
- **Estação meteorológica** (Java 21) e **sensores de solo** e **válvulas** (Python).
- **CLI** e **ponte do painel** (Python), ambos clientes TCP do gateway.
- **Interface web** (Next.js, TypeScript e shadcn/ui).

A arquitetura e o protocolo estão descritos em [docs/arquitetura.md](docs/arquitetura.md).

## Executando

Requer Docker com Compose, em Linux. Os serviços usam a rede do host porque a bridge
padrão do Docker não encaminha multicast.

```bash
docker compose up -d --build
```

O painel fica em <http://localhost:8080>. Em poucos segundos as cinco fontes aparecem:
`estacao-01`, `solo-a`, `solo-b`, `valvula-a` e `valvula-b`.

O mesmo pode ser feito pela linha de comando:

```bash
docker compose run --rm client list
docker compose run --rm client valve valvula-a --open --flow 30
docker compose run --rm client valve valvula-b --disable   # para a telemetria, simulando falha
docker compose run --rm client valve valvula-b --enable
docker compose run --rm client query driest --window 60   # também: water, temp, alerts
docker compose run --rm client watch
```

`docker compose down` encerra tudo. O histórico continua no volume `gateway-data`.

## Portas

| Porta | Protocolo | Uso |
|---|---|---|
| `239.255.10.1:9999` | UDP multicast | descoberta das fontes |
| `9100` | UDP | anúncios e leituras recebidos pelo gateway |
| `9200` | TCP | CLI e ponte do painel (frames de 4 bytes + Protobuf) |
| `50061`, `50062` | gRPC | válvulas A e B |
| `8080` | HTTP | painel web, eventos SSE e API JSON |

## Desenvolvimento

O código gerado a partir de `proto/agro.proto` fica em `gen/` e não deve ser editado à mão.
Com Go, Python, uv, protoc e Task instalados (`mise install` cuida disso):

```bash
task proto   # gera gen/go e gen/python
task test    # go test e pytest
task lint    # go vet, gofmt e ruff
```

Sem as ferramentas no host, use a imagem `docker/devtools.Dockerfile`:

```bash
docker build -t agromesh-devtools -f docker/devtools.Dockerfile docker
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD":/src -w /src agromesh-devtools \
  bash -c 'go test ./... && /opt/py/bin/python -m pytest -q && /opt/py/bin/ruff check .'
```

A estação Java é compilada com Maven (`mvn -B -f sources/weather/pom.xml package`), que
também gera as classes Protobuf.

A interface está em `web/`. O `next build` gera um site estático em `web/out`, servido pela
ponte `dashboard/server.py`. Para trabalhar nela com recarga automática, com o restante do
sistema rodando:

```bash
cd web && npm ci && npm run dev   # http://localhost:3000; /events e /api vão para :8080
```
