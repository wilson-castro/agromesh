# Como rodar o AgroMesh

O AgroMesh simula uma fazenda com sensores e válvulas de irrigação e mostra tudo num painel no navegador. Este guia explica como ligar e desligar o sistema.

## O que você precisa

Um computador com Linux e o Docker instalado. O Docker é um programa que roda cada parte do sistema isolada das outras, sem você precisar instalar mais nada. Se ainda não tem, siga o [guia oficial de instalação](https://docs.docker.com/engine/install/).

## Ligar

Abra o terminal na pasta do AgroMesh e digite o comando abaixo.

```bash
./iniciar.sh
```

Na primeira vez ele demora alguns minutos, porque prepara tudo do zero. Nas próximas, leva poucos segundos. Quando aparecer a mensagem "Pronto", abra <http://localhost:8080> no navegador.

O painel mostra cinco equipamentos simulados.

| Nome | O que é |
|---|---|
| `estacao-01` | Estação meteorológica, que mede temperatura, umidade do ar, vento e chuva. |
| `solo-a` e `solo-b` | Sensores que medem a umidade da terra de cada talhão (cada área de plantio). |
| `valvula-a` e `valvula-b` | Válvulas de irrigação, que podem ser abertas e fechadas pelo painel. |

## Desligar

```bash
./iniciar.sh parar
```

Os dados coletados ficam guardados e voltam a aparecer na próxima vez que você ligar.

## Se algo der errado

O script avisa o que aconteceu e o que fazer. Os casos mais comuns são estes.

- "o Docker não está instalado". Instale o Docker pelo guia indicado acima.
- "o Docker não respondeu". Ligue o Docker, ou rode `sudo ./iniciar.sh`.
- "a porta 8080 já está em uso". Outro programa está usando o endereço do painel. Feche esse programa e rode de novo. Isso acontece, por exemplo, quando o DataMesh está aberto ao mesmo tempo.

Para ver os detalhes técnicos de um erro, rode `docker compose logs`.

## Para saber mais

O [docs/negocio.md](docs/negocio.md) explica o que o sistema faz na fazenda. O [docs/arquitetura.md](docs/arquitetura.md) e o [docs/servicos.md](docs/servicos.md) explicam como ele funciona por dentro.
