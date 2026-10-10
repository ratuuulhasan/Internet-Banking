"""
Multilingual embeddings optimized for Bangla + English.
Uses LaBSE — excellent for Bengali semantic search.
"""
from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self):
        if self._model is None:
            print("⏳ Loading LaBSE embedding model...")
            # LaBSE works well for Bengali (per GitHub reference)
            self._model = SentenceTransformer('sentence-transformers/LaBSE')
            print("✅ Embedding model loaded")
        return self._model

    def embed(self, texts):
        """Embed a list of texts. Returns numpy array."""
        model = self.load()
        if isinstance(texts, str):
            texts = [texts]
        return model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

    def embed_query(self, text):
        """Embed a single query."""
        return self.embed([text])[0]


embeddings = EmbeddingService()