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
