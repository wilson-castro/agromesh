# AgroMesh

Monitoramento e irrigação de uma fazenda dividida em talhões. Sensores e válvulas são
processos independentes que o gateway encontra por multicast, recebem comandos via gRPC e
enviam telemetria por UDP. Um painel web mostra tudo em tempo real.

- O **gateway** (Go) descobre as fontes, recebe as leituras, guarda o histórico em SQLite, responde consultas e repassa comandos às válvulas por gRPC.
- **Estação meteorológica** (Java 21) e **sensores de solo** e **válvulas** (Python).
- **CLI** e **ponte do painel** (Python), ambos clientes TCP do gateway.
- **Interface web** (Next.js, TypeScript e a biblioteca de componentes `shadcn/ui`).

A documentação fica em `docs/`.

- [docs/negocio.md](docs/negocio.md) explica o problema da fazenda e o que o painel permite fazer.
- [docs/arquitetura.md](docs/arquitetura.md) mostra como as partes se conectam e que mensagens trocam.
- [docs/servicos.md](docs/servicos.md) descreve cada programa, com portas e configurações.

## Executando

Para só ligar e usar o sistema, siga o [COMO-RODAR.md](COMO-RODAR.md). O `./iniciar.sh` sobe tudo e espera o painel e as fontes ficarem prontos, e `./iniciar.sh parar` encerra.

Requer Docker com Compose, em Linux. Os serviços usam a rede do host porque a bridge
padrão do Docker não encaminha multicast.

```bash
docker compose up -d --build
```

O painel fica em <http://localhost:8080>. Em poucos segundos aparecem as cinco fontes,
`estacao-01`, `solo-a`, `solo-b`, `valvula-a` e `valvula-b`.

Os comandos abaixo fazem o mesmo pela linha de comando.

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

## Por que cada tecnologia

Esta seção explica em poucas linhas por que cada peça foi escolhida.

### Linguagens

- O gateway é escrito em Go por causa das goroutines, tarefas leves que o Go executa em paralelo. Com elas, o gateway atende muitas conexões TCP e UDP ao mesmo tempo sem código complicado. O resultado é um único binário estático, o que deixa a imagem Docker pequena.
- A estação meteorológica é escrita em Java 21 para mostrar que fontes em linguagens diferentes conversam com o mesmo gateway. Um `ScheduledExecutorService` dispara o envio das leituras em intervalos fixos.
- Sensores de solo, válvulas, CLI e ponte do painel são escritos em Python 3.12. Simular sensores e escrever ferramentas é rápido nessa linguagem, e ela tem bibliotecas oficiais de gRPC e Protobuf. O resto usa só a biblioteca padrão.
- A interface web usa Next.js com TypeScript e componentes prontos do shadcn/ui. O build gera arquivos estáticos em `web/out`, servidos pela própria ponte do painel, então não há servidor Node rodando em produção.

### Comunicação

- O Protocol Buffers (Protobuf) é um formato binário com esquema definido em arquivo. Um único `proto/agro.proto` gera os tipos para Go, Java e Python. As mensagens ficam menores que em JSON, e campos novos podem ser adicionados sem quebrar quem já usa o esquema.
- O UDP multicast em `239.255.10.1:9999` serve para a descoberta. Multicast envia um pacote para um grupo de endereços, e todas as fontes inscritas no grupo recebem. Assim nenhum processo precisa conhecer o endereço dos outros de antemão.
- As leituras chegam por UDP na porta `9100`. Telemetria periódica tolera a perda de um pacote, porque a próxima leitura chega em seguida. Com isso o sistema evita o custo de abrir e manter conexões.
- A CLI e a ponte do painel usam TCP na porta `9200`. Consultas e comandos precisam chegar inteiros e na ordem certa, e o TCP entrega isso.
- Cada mensagem no TCP vai em um frame de 4 bytes seguido do Protobuf. O TCP entrega um fluxo contínuo de bytes e não separa as mensagens, e o Protobuf também não marca onde uma mensagem termina. Por isso cada mensagem começa com um `uint32` big-endian que informa o tamanho dela. Quem recebe lê esses 4 bytes e depois exatamente esse número de bytes, sem juntar duas mensagens nem cortar uma ao meio. Os 4 bytes comportam mensagens de até 4 GiB e são simples de ler em Go, Java e Python.
- As válvulas recebem comandos por gRPC nas portas `50061` e `50062`. O gRPC é um sistema de chamada remota em que um processo chama uma função de outro como se fosse local. Abrir ou fechar uma válvula é exatamente uma chamada com resposta, e o gRPC já traz contrato tipado, prazo de resposta e códigos de erro.
- O painel recebe atualizações por SSE (Server-Sent Events). O navegador não fala Protobuf sobre TCP, e o SSE permite que o servidor envie eventos para a página por HTTP comum, sem WebSocket.

### Persistência e infraestrutura

- O histórico fica em SQLite, um banco de dados guardado em um único arquivo, sem servidor separado. O driver `modernc.org/sqlite` é escrito em Go puro e dispensa cgo, a ponte entre Go e código C. Isso mantém o build e a imagem simples.
- O Docker Compose sobe gateway, fontes, CLI e painel com um único comando. Cada serviço roda em seu próprio contêiner, simulando máquinas separadas.
- `uv`, `mise`, `Taskfile`, `ruff` e `pytest` fixam as versões das ferramentas. Assim os comandos de geração de código, teste e lint são iguais para todo o grupo.

## Desenvolvimento

O código gerado a partir de `proto/agro.proto` fica em `gen/` e não deve ser editado à mão.
Com Go, Python, uv, protoc e Task instalados (`mise install` cuida disso), estes comandos geram o código, rodam os testes e o lint.

```bash
task proto   # gera gen/go e gen/python
task test    # go test e pytest
task lint    # go vet, gofmt e ruff
```

Sem as ferramentas no host, use a imagem `docker/devtools.Dockerfile`, como abaixo.

```bash
docker build -t agromesh-devtools -f docker/devtools.Dockerfile docker
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD":/src -w /src agromesh-devtools \
  bash -c 'go test ./... && /opt/py/bin/python -m pytest -q && /opt/py/bin/ruff check .'
```

A estação Java é compilada com Maven (`mvn -B -f sources/weather/pom.xml package`), que
também gera as classes Protobuf.

A interface está em `web/`. O `next build` gera um site estático em `web/out`, servido pela
ponte `dashboard/server.py`. Para trabalhar nela com recarga automática, deixe o restante do
sistema rodando e use o comando abaixo.

```bash
cd web && npm ci && npm run dev   # http://localhost:3000; /events e /api vão para :8080
```
