#!/usr/bin/env bash
# Sobe o AgroMesh inteiro com Docker e espera o painel e as fontes ficarem prontos.
# ./iniciar.sh sobe tudo, e ./iniciar.sh parar encerra tudo.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

PAINEL="http://localhost:8080"
FONTES=5

falha() {
    echo ""
    echo "ERRO: $1"
    exit 1
}

porta_aberta() {
    (exec 3<>/dev/tcp/127.0.0.1/8080) 2>/dev/null
}

conferir_docker() {
    command -v docker >/dev/null 2>&1 ||
        falha "o Docker não está instalado. Veja https://docs.docker.com/engine/install/"
    docker info >/dev/null 2>&1 ||
        falha "o Docker está instalado, mas não respondeu. Ligue o Docker ou rode o script com sudo."
    docker compose version >/dev/null 2>&1 ||
        falha "falta o Docker Compose. Instale o pacote docker-compose-plugin."
}

conferir_porta() {
    # A porta 8080 ocupada por outro programa impediria o painel de abrir.
    if porta_aberta && [[ -z "$(docker compose ps -q dashboard 2>/dev/null)" ]]; then
        falha "a porta 8080 já está em uso por outro programa. Feche esse programa e tente de novo."
    fi
}

esperar_painel() {
    for _ in $(seq 60); do
        porta_aberta && return 0
        sleep 1
    done
    falha "o painel não abriu em 60 s. Veja os erros com: docker compose logs"
}

esperar_fontes() {
    local online=0
    for _ in $(seq 20); do
        online=$(docker compose run --rm -T client list 2>/dev/null | grep -c " online " || true)
        [[ "$online" -ge "$FONTES" ]] && return 0
        sleep 2
    done
    echo "Aviso: só $online de $FONTES fontes apareceram. O painel funciona, mas confira com: docker compose logs"
}

if [[ "${1:-}" == "parar" ]]; then
    conferir_docker
    docker compose down
    echo "AgroMesh encerrado."
    exit 0
fi

conferir_docker
conferir_porta

echo "Preparando e iniciando o AgroMesh. Na primeira vez isso leva alguns minutos..."
docker compose up -d --build

echo "Esperando o painel abrir..."
esperar_painel
echo "Esperando as fontes se conectarem..."
esperar_fontes

echo ""
echo "Pronto. Abra o painel no navegador: $PAINEL"
echo "Para encerrar: ./iniciar.sh parar"
