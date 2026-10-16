# AgroMesh

Fazenda inteligente com monitoramento e irrigação por talhão: sockets TCP/UDP,
descoberta multicast, Protobuf e controle gRPC.
Gateway em Go e estação meteorológica em Java 21; sensores de solo, válvulas, CLI e dashboard em Python.

## Executar com Docker

Pré-requisitos: Docker Engine e Compose em Linux, com acesso ao daemon. A rede do host
é usada porque a bridge padrão não encaminha a descoberta multicast. As portas abaixo
precisam estar livres; outro sistema usando o mesmo grupo multicast deve estar parado.

```bash
docker compose up -d --build
docker compose ps
docker compose run --rm client list
```

Abra <http://localhost:8080>. Aguarde alguns segundos pela descoberta das cinco fontes:
`estacao-01`, `solo-a`, `solo-b`, `valvula-a` e `valvula-b`.
São sete serviços persistentes incluindo gateway e dashboard.
O painel segue o tema claro/escuro do sistema e reúne indicadores, gráficos, alertas,
controle das válvulas e consultas históricas em uma tela.

```bash
# Controle: cliente TCP → gateway → gRPC da válvula
docker compose run --rm client valve valvula-a --open --flow 30 --interval 2
docker compose run --rm client valve valvula-a --close
# Falha simulada: cessa telemetria; gRPC continua disponível para reativação
docker compose run --rm client valve valvula-b --disable
docker compose run --rm client valve valvula-b --enable
# Consultas: janela em minutos
docker compose run --rm client query driest --window 60
docker compose run --rm client query water --window 60
docker compose run --rm client query temp --window 60
docker compose run --rm client query alerts --window 60
# Assinatura contínua; Ctrl+C encerra
docker compose run --rm client watch
```

Para inspecionar problemas: `docker compose logs --tail=100 gateway solo-a valvula-a dashboard`.
Para parar: `docker compose stop`; para retomar: `docker compose up -d`.
O histórico SQLite permanece no volume `gateway-data`. Reiniciar uma válvula reinicia
seu contador de litros; veja as limitações em [docs/arquitetura.md](docs/arquitetura.md).

## Componentes e portas

| Processo | Transporte | Finalidade |
|---|---|---|
| Descoberta | UDP multicast `239.255.10.1:9999` | Gateway procura fontes |
| Gateway | UDP `9100` | Anúncios e leituras Protobuf |
| Gateway | TCP `9200` | CLI e dashboard; frames de 4 bytes big-endian + Protobuf |
| Válvulas A/B | gRPC `50061` / `50062` | Consulta e configuração pelo gateway |
| Dashboard | HTTP `8080` | Página e eventos SSE para o navegador |

O CLI e o servidor do dashboard acessam somente o gateway via TCP. O navegador acessa
somente o servidor HTTP do dashboard. O contrato distribuído está em `proto/agro.proto`;
o trecho web usa JSON/SSE como adaptação de apresentação.
A estação Java usa classes geradas pelo Maven a partir do mesmo `.proto`, em
`sources/weather/target/generated-sources/protobuf/java` (não editar à mão).

## Desenvolvimento e verificações

Com Go 1.23, Python 3.12+, uv, protoc, plugins Go do Protobuf/gRPC e Task já disponíveis:

```bash
task proto
task test
task lint
```

A preparação de dependências (`task deps`) instala pacotes e deve ser executada apenas
com autorização do responsável pelo ambiente. `gen/` contém código gerado: não editar à mão.
Sem Go ou protoc no host, use a imagem de ferramentas em Docker. O lint Python precisa de
Ruff disponível; o Dockerfile da toolchain inclui pytest e Ruff. Reconstrua a imagem
para disponibilizar o verificador: `docker build -t agromesh-devtools -f docker/devtools.Dockerfile docker`.
Execute o lint com:

```bash
docker run --rm -v "$PWD":/src -w /src agromesh-devtools /opt/py/bin/ruff check .
```

A estação Java requer JDK 21 e Maven para execução local: `task weather`.
`mvn -B -f sources/weather/pom.xml package` gera o Protobuf e compila o JAR.
O build Docker do serviço `estacao` faz essas etapas automaticamente.
A primeira compilação Maven baixa dependências e o compilador Protobuf.
