# Serviços

Este documento descreve cada programa do AgroMesh. Para cada um, diz o que ele faz, onde está o código, que portas usa e o que pode ser configurado. Para a visão de conjunto, leia [arquitetura.md](arquitetura.md).

A configuração é feita por variáveis de ambiente, que são valores passados ao programa quando ele inicia. No Docker, elas ficam no `docker-compose.yml`. Na tabela de cada serviço, o valor padrão é o usado quando a variável não é definida.

Para ver o que um serviço está fazendo, use `docker compose logs -f` seguido do nome dele, por exemplo `docker compose logs -f gateway`.

## Gateway

O Gateway é o centro do sistema, escrito em Go. O código fica em `gateway/`.

Ele faz cinco coisas ao mesmo tempo.

- Envia o pedido de descoberta ao grupo multicast ao iniciar e a cada 15 s (`main.go`).
- Recebe anúncios e leituras por UDP e repassa cada um ao lugar certo (`main.go`).
- Mantém a lista de fontes, com a última leitura e o estado online ou offline (`registry.go`). A cada 2 s, marca como offline quem ficou em silêncio por tempo demais.
- Grava as leituras no SQLite e calcula as consultas (`store.go`).
- Atende o CLI e a ponte do painel por TCP (`tcpserver.go`). Os comandos às válvulas saem por gRPC (`control.go`). Os eventos ao vivo vão para quem assinou (`hub.go`).

O `hub.go` guarda até 256 mensagens por assinante. Se um assinante ficar lento demais, as mensagens que não cabem são descartadas, para a recepção de dados não travar. O `control.go` reaproveita uma conexão gRPC por válvula e desiste de um comando que demora mais de 3 s.

| Variável | Padrão | O que define |
|---|---|---|
| `GATEWAY_UDP_PORT` | `9100` | Porta onde recebe anúncios e leituras. |
| `GATEWAY_TCP_PORT` | `9200` | Porta onde atende o CLI e a ponte do painel. |
| `MCAST_ADDR` | `239.255.10.1:9999` | Grupo multicast da descoberta. |
| `DISCOVERY_INTERVAL_S` | `15` | Segundos entre pedidos de descoberta. |
| `DB_PATH` | `agromesh.db` | Arquivo do banco. No Docker é `/data/agromesh.db`. |
| `ADVERTISE_IP` | IP da máquina | Endereço que o Gateway informa às fontes. |

## Estação meteorológica

A estação é uma fonte contínua, escrita em Java 21. O código fica em `sources/weather/`, e o Maven (a ferramenta de build do Java) também gera as classes do Protobuf.

A cada intervalo, ela envia quatro métricas.

| Métrica | Simulação |
|---|---|
| `temperature_c` | Oscila entre cerca de 21 °C e 33 °C num ciclo de 5 minutos. |
| `air_humidity_pct` | Cai quando a temperatura sobe, entre 20% e 100%. |
| `wind_kmh` | Varia em torno de 12 km/h. |
| `rain_mm` | Quase sempre zero. Em cerca de 5% das leituras chove até 4 mm. |

A estação não aceita comandos.

| Variável | Padrão | O que define |
|---|---|---|
| `SOURCE_ID` | `estacao-01` | Nome da fonte. |
| `FIELD_ID` | `sede` | Local onde está instalada. |
| `INTERVAL_S` | `3` | Segundos entre leituras. |
| `MCAST_ADDR` | `239.255.10.1:9999` | Grupo multicast da descoberta. |
| `ADVERTISE_IP` | IP da máquina | Endereço que a estação informa ao Gateway. |

## Sensor de solo

O sensor de solo é uma fonte orientada a eventos, escrita em Python. O código fica em `sources/soil/main.py`. Há um por talhão (`solo-a` e `solo-b`).

Ele mede a terra a cada segundo e envia `moisture_pct` (umidade) e `soil_temp_c` (temperatura do solo) no intervalo configurado. A umidade oscila em torno de 32%, entre cerca de 20% e 44%, num ciclo de 4 minutos. Cada sensor começa o ciclo num ponto diferente, para os talhões não secarem ao mesmo tempo.

Quando a umidade cai abaixo do limite de seca, o sensor envia na hora uma leitura de alerta, sem esperar o próximo envio. Ele só alerta de novo depois que a umidade sobe 2 pontos acima do limite. O sensor não aceita comandos.

| Variável | Padrão | O que define |
|---|---|---|
| `SOURCE_ID` | `solo-a` | Nome da fonte. |
| `FIELD_ID` | `talhao-a` | Talhão onde está instalado. |
| `INTERVAL_S` | `5` (no Docker, `4`) | Segundos entre leituras periódicas. |
| `DRY_THRESHOLD` | `25` | Umidade, em %, abaixo da qual o sensor alerta. |

## Válvula de irrigação

A válvula é a fonte controlável, escrita em Python. O código fica em `sources/valve/main.py`. Há uma por talhão (`valvula-a` na porta 50061 e `valvula-b` na 50062).

Ela começa fechada. Enquanto está aberta e ativa, soma a cada segundo os litros que passaram, de acordo com a vazão. Ela envia três métricas. A `open` vale 1 quando está aberta e 0 quando está fechada. A `flow_lpm` é a vazão atual, em litros por minuto. A `liters_total` soma os litros desde que a válvula ligou. Depois de cada comando, envia uma leitura na hora com o estado novo.

O serviço gRPC `IrrigationValve` tem dois métodos. O `GetState` devolve o estado atual. O `Configure` aplica um comando e devolve o estado novo. O comando pode abrir ou fechar a válvula, mudar a vazão, mudar o intervalo de envio ou desativar a válvula para simular um defeito. Desativada, ela para de enviar dados e corta a água, mas continua aceitando comandos.

| Variável | Padrão | O que define |
|---|---|---|
| `SOURCE_ID` | `valvula-a` | Nome da fonte. |
| `FIELD_ID` | `talhao-a` | Talhão que irriga. |
| `GRPC_PORT` | qualquer porta livre | Porta do serviço gRPC. No Docker, `50061` e `50062`. |
| `FLOW_LPM` | `20` (no Docker, `25` e `18`) | Vazão inicial, em litros por minuto. |
| `INTERVAL_S` | `2` | Segundos entre leituras. |

## Código comum das fontes Python

O sensor e a válvula usam o mesmo código para a descoberta, em `common/source_runtime.py`. Ele escuta o grupo multicast, guarda o endereço do Gateway e responde com o anúncio da fonte. Também envia os pacotes UDP e descarta as leituras enquanto o Gateway ainda é desconhecido.

O `common/gateway_client.py` é o cliente TCP usado pelo CLI e pela ponte do painel. O `common/framing.py` cuida dos 4 bytes de tamanho antes de cada mensagem.

## CLI

O CLI é um programa de terminal escrito em Python. O código fica em `client/main.py`. No Docker, ele roda sob demanda com `docker compose run --rm client` seguido do comando.

| Comando | O que faz |
|---|---|
| `list` | Lista as fontes, com tipo, talhão, estado, endereço e última leitura. |
| `valve valvula-a --open --flow 30` | Abre a válvula com vazão de 30 L/min. Também aceita `--close`, `--enable`, `--disable` e `--interval`. |
| `query driest --window 60` | Faz uma consulta na janela em minutos. Os tipos são `driest`, `water`, `temp` e `alerts`. |
| `watch` | Mostra as leituras e as mudanças de fontes ao vivo, até ser interrompido com Ctrl+C. |

O CLI encontra o Gateway por `GATEWAY_HOST` (padrão `127.0.0.1`) e `GATEWAY_TCP_PORT` (padrão `9200`).

## Ponte do painel

A ponte liga o navegador ao Gateway e é escrita em Python. O código fica em `dashboard/server.py`.

Ela mantém uma assinatura TCP no Gateway e tenta de novo a cada 2 s se ele cair. Também guarda na memória as últimas 400 leituras de cada fonte (cerca de 10 minutos) e os últimos 50 alertas. Assim, quem abre o painel já vê os gráficos preenchidos.

| Endereço | O que faz |
|---|---|
| `/` | Entrega a interface web, que fica pronta em `web/out`. |
| `/events` | Fluxo SSE com o estado inicial e depois cada leitura e mudança de fontes. |
| `/api/command` | Recebe um comando de válvula em JSON e repassa ao Gateway. |
| `/api/query?kind=driest&window=60` | Faz uma consulta e devolve o resultado em JSON. |

| Variável | Padrão | O que define |
|---|---|---|
| `DASHBOARD_PORT` | `8080` | Porta do painel. |
| `GATEWAY_HOST` | `127.0.0.1` | Endereço do Gateway. |
| `GATEWAY_TCP_PORT` | `9200` | Porta TCP do Gateway. |
| `WEB_ROOT` | `web/out` | Pasta com a interface pronta. |

## Interface web

A interface é o painel no navegador, feito com Next.js, TypeScript e os componentes shadcn/ui. O código fica em `web/`. Ela é gerada como um site estático, que a ponte entrega.

A tela mostra, de cima para baixo, estas partes.

- Indicadores com fontes online, umidade média do solo, temperatura do ar, água aplicada e alertas desde que o painel abriu.
- Três gráficos dos últimos 5 minutos. Eles mostram a umidade do solo por talhão, com a linha do limite de 25%, a vazão das válvulas e a temperatura do ar.
- A lista de fontes, com os controles das válvulas, e a lista de alertas recentes.
- As consultas, com escolha da janela de 5 minutos, 15 minutos, 1 hora ou 24 horas.

Para mexer na interface com recarga automática, veja a seção de desenvolvimento do [README](../README.md).
