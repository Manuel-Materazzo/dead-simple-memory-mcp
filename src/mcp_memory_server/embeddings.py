"""Embedding model management with background loading."""

import struct
import threading
from typing import Optional

from sentence_transformers import SentenceTransformer

from mcp_memory_server.config import get_embedding_model

_model: Optional[SentenceTransformer] = None
_model_ready = threading.Event()
_model_error: Optional[Exception] = None


def _load_model() -> None:
    """Load the embedding model in the background."""
    global _model, _model_error
    try:
        model_name = get_embedding_model()
        _model = SentenceTransformer(model_name)
        _model_ready.set()
    except Exception as e:
        _model_error = e
        _model_ready.set()


def start_model_loading() -> None:
    """Start loading the embedding model in a background thread."""
    thread = threading.Thread(target=_load_model, daemon=True)
    thread.start()


def get_embedding(text: str) -> list[float]:
    """Get the embedding for a text string. Blocks until model is ready."""
    _model_ready.wait()
    if _model_error:
        raise _model_error
    if _model is None:
        raise RuntimeError("Model not loaded")
    embedding = _model.encode(text, convert_to_numpy=True)
    result: list[float] = embedding.tolist()
    return result


def embedding_to_blob(embedding: list[float]) -> bytes:
    """Convert embedding list to bytes for SQLite storage."""
    return struct.pack(f"{len(embedding)}f", *embedding)


def blob_to_embedding(blob: bytes) -> list[float]:
    """Convert bytes from SQLite back to embedding list."""
    num_floats = len(blob) // 4
    return list(struct.unpack(f"{num_floats}f", blob))


def is_model_ready() -> bool:
    """Check if the model is ready for use."""
    return _model_ready.is_set() and _model_error is None
