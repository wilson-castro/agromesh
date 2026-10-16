# Build estático do frontend (Next.js); só o resultado em out/ vai para a imagem final.
FROM node:22-bookworm-slim AS web
ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web ./
RUN npm run build

# Imagem única dos processos Python; o comando define qual processo roda.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir "grpcio>=1.67.1" "protobuf>=5.28.3"
COPY common common
COPY gen/python gen/python
COPY sources sources
COPY client client
COPY dashboard dashboard
COPY --from=web /web/out web/out
