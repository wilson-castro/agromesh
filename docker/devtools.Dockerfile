# Toolchain para gerar protos e testar sem instalar Go/protoc no host.
# Build: docker build -t agromesh-devtools -f docker/devtools.Dockerfile docker
FROM python:3.12-bookworm
COPY --from=golang:1.23-bookworm /usr/local/go /usr/local/go
ENV GOPATH=/go \
    GOBIN=/usr/local/bin \
    PATH=/usr/local/go/bin:/go/bin:$PATH
RUN apt-get update && apt-get install -y --no-install-recommends protobuf-compiler && rm -rf /var/lib/apt/lists/*
RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.35.1 && go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.5.1
RUN python3 -m venv /opt/py && /opt/py/bin/pip install --no-cache-dir grpcio==1.67.1 grpcio-tools==1.67.1 protobuf==5.28.3 pytest ruff
RUN chmod -R a+rwX /go
