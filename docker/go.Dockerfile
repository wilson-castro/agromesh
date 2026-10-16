# Imagem do gateway.
FROM golang:1.23-bookworm AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY gen/go gen/go
COPY internal internal
COPY gateway gateway
# CGO desligado: o driver SQLite (modernc) é Go puro, então o binário é estático.
RUN CGO_ENABLED=0 go build -o /out/gateway ./gateway

FROM gcr.io/distroless/static-debian12
COPY --from=build /out/gateway /gateway
ENTRYPOINT ["/gateway"]
