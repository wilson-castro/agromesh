"""Ponto único de import das classes geradas a partir de proto/agro.proto."""

# common/__init__.py inclui gen/python no sys.path antes destes imports.
import agro_pb2 as pb
import agro_pb2_grpc as pb_grpc

__all__ = ["pb", "pb_grpc"]
