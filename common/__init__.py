"""Código compartilhado pelos processos Python (fontes, cliente e dashboard)."""

import sys
from pathlib import Path

# O protoc gera `agro_pb2_grpc.py` com `import agro_pb2` absoluto; por isso o
# diretório gerado precisa estar no sys.path antes de qualquer import dele.
_GEN_PYTHON = Path(__file__).resolve().parent.parent / "gen" / "python"
if str(_GEN_PYTHON) not in sys.path:
    sys.path.insert(0, str(_GEN_PYTHON))
