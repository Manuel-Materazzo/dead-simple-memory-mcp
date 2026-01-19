"""Tests for embedding operations."""

import pytest

from mcp_memory_server.embeddings import (
    blob_to_embedding,
    embedding_to_blob,
    get_embedding,
    start_model_loading,
)


@pytest.fixture(scope="module", autouse=True)
def load_model():
    """Load the embedding model before tests."""
    start_model_loading()


class TestEmbeddings:
    def test_get_embedding(self):
        """Test generating an embedding from text."""
        embedding = get_embedding("Hello world")
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)

    def test_embedding_consistency(self):
        """Test that the same text produces the same embedding."""
        text = "This is a test sentence"
        embedding1 = get_embedding(text)
        embedding2 = get_embedding(text)
        assert embedding1 == embedding2

    def test_embedding_blob_conversion(self):
        """Test converting embeddings to and from blobs."""
        original = get_embedding("Test text")
        blob = embedding_to_blob(original)
        recovered = blob_to_embedding(blob)
        
        assert len(recovered) == len(original)
        for a, b in zip(original, recovered):
            assert abs(a - b) < 1e-6

    def test_different_texts_different_embeddings(self):
        """Test that different texts produce different embeddings."""
        embedding1 = get_embedding("I love cats")
        embedding2 = get_embedding("The stock market crashed")
        
        assert embedding1 != embedding2
