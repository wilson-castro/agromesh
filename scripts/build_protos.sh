#!/usr/bin/env bash
# Gera o código Protobuf/gRPC para Go e Python a partir de proto/agro.proto.
set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p gen/go gen/python

protoc -I proto \
  --go_out=. --go_opt=module=agromesh \
  --go-grpc_out=. --go-grpc_opt=module=agromesh \
  proto/agro.proto

# Para Python o grpcio-tools traz o protoc embutido, alinhado ao runtime.
uv run python -m grpc_tools.protoc -I proto \
  --python_out=gen/python --grpc_python_out=gen/python --pyi_out=gen/python \
  proto/agro.proto

echo "protos gerados em gen/go e gen/python"
