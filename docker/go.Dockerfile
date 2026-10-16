# Imagem do gateway Go. TARGET escolhe o pacote.
FROM golang:1.23-bookworm AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY gen/go gen/go
COPY internal internal
COPY gateway gateway
ARG TARGET
# CGO desligado: o driver SQLite (modernc) é Go puro, então o binário é estático.
RUN CGO_ENABLED=0 go build -o /out/app ./${TARGET}

FROM gcr.io/distroless/static-debian12
COPY --from=build /out/app /app
ENTRYPOINT ["/app"]
