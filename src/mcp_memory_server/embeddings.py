"""Embedding model management with background loading."""

import struct
import threading
from typing import Optional

from sentence_transformers import SentenceTransformer

from mcp_memory_server.config import get_embedding_model, is_async_model_loading

_model: Optional[SentenceTransformer] = None
_model_name: Optional[str] = None
_model_dimension: Optional[int] = None
_model_ready = threading.Event()
_model_error: Optional[Exception] = None


def _load_model() -> None:
    """Load the embedding model in the background."""
    global _model, _model_error, _model_name, _model_dimension
    try:
        model_name = get_embedding_model()
        _model = SentenceTransformer(model_name)
        _model_name = model_name
        _model_dimension = _model.get_sentence_embedding_dimension()
        _model_ready.set()
    except Exception as e:
        _model_error = e
        _model_ready.set()


def start_model_loading() -> None:
    """Start loading the embedding model.

    If MEMORY_ASYNC_MODEL_LOADING is true (default), loads in a background daemon thread.
    If false, loads synchronously (blocking startup).
    """
    if is_async_model_loading():
        thread = threading.Thread(target=_load_model, daemon=True)
        thread.start()
    else:
        _load_model()


def get_embedding(text: str) -> list[float]:
    """Get the embedding for a text string. Blocks until model is ready.

    Returns a normalized embedding (L2 norm = 1) so that L2 distance
    is equivalent to cosine distance for KNN queries in sqlite-vec.
    """
    _model_ready.wait()
    if _model_error:
        raise _model_error
    if _model is None:
        raise RuntimeError("Model not loaded")
    embedding = _model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
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


def get_model_info() -> tuple[str, int]:
    """Get the loaded model name and dimension. Blocks until model is ready.

    Returns:
        Tuple of (model_name, embedding_dimension)
    """
    _model_ready.wait()
    if _model_error:
        raise _model_error
    if _model_name is None or _model_dimension is None:
        raise RuntimeError("Model not loaded")
    return _model_name, _model_dimension


def wait_for_model() -> None:
    """Block until the embedding model is ready."""
    _model_ready.wait()
    if _model_error:
        raise _model_error
