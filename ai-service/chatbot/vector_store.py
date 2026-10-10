"""
FAISS vector store for RAG.
Indexes the banking knowledge base once, then serves fast retrieval.
"""
import os
import pickle
import numpy as np
import faiss
from pathlib import Path
from .embeddings import embeddings

BASE_DIR = Path(__file__).resolve().parent.parent
KB_DIR = BASE_DIR / 'chatbot' / 'knowledge_base'
INDEX_DIR = BASE_DIR / 'models' / 'chatbot'
INDEX_DIR.mkdir(parents=True, exist_ok=True)

INDEX_PATH = INDEX_DIR / 'faiss.index'
META_PATH = INDEX_DIR / 'chunks.pkl'


def chunk_text(text, chunk_size=400, overlap=80):
    """Split text into overlapping chunks (Bangla-friendly char-based)."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def load_knowledge_base():
    """Load all markdown files and chunk them."""
    chunks = []
    metadata = []
    for md_file in KB_DIR.glob('*.md'):
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        lang = 'bn' if 'bangla' in md_file.name else 'en'
        # Split by ## sections for better granularity
        sections = content.split('\n## ')
        for i, section in enumerate(sections):
            if not section.strip():
                continue
            text = section if i == 0 else f"## {section}"
            for chunk in chunk_text(text, chunk_size=350, overlap=60):
                if len(chunk.strip()) > 30:
                    chunks.append(chunk.strip())
                    metadata.append({
                        'source': md_file.name,
                        'language': lang,
                        'chunk_id': len(chunks) - 1,
                    })
    return chunks, metadata


class VectorStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.index = None
            cls._instance.chunks = []
            cls._instance.metadata = []
        return cls._instance

    def build(self, force=False):
        """Build FAISS index from knowledge base."""
        if not force and INDEX_PATH.exists() and META_PATH.exists():
            self.load()
            return

        print("🏗️ Building FAISS index...")
        chunks, metadata = load_knowledge_base()
        print(f"   Chunks: {len(chunks)}")

        vectors = embeddings.embed(chunks)
        dim = vectors.shape[1]

        # IndexFlatL2 — fast + accurate for small KB
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(vectors.astype('float32'))
        self.chunks = chunks
        self.metadata = metadata

        # Persist
        faiss.write_index(self.index, str(INDEX_PATH))
        with open(META_PATH, 'wb') as f:
            pickle.dump({'chunks': chunks, 'metadata': metadata}, f)
        print(f"✅ FAISS index built ({len(chunks)} chunks, dim={dim})")

    def load(self):
        """Load FAISS index from disk."""
        self.index = faiss.read_index(str(INDEX_PATH))
        with open(META_PATH, 'rb') as f:
            data = pickle.load(f)
            self.chunks = data['chunks']
            self.metadata = data['metadata']
        print(f"✅ FAISS loaded ({len(self.chunks)} chunks)")

    def search(self, query, top_k=4, lang_filter=None):
        """Return top_k most relevant chunks."""
        if self.index is None:
            self.build()

        q_vec = embeddings.embed_query(query).astype('float32').reshape(1, -1)
        distances, indices = self.index.search(q_vec, top_k * 2)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1 or idx >= len(self.chunks):
                continue
            meta = self.metadata[idx]
            if lang_filter and meta.get('language') != lang_filter:
                continue
            results.append({
                'text': self.chunks[idx],
                'distance': float(dist),
                'source': meta.get('source'),
                'language': meta.get('language'),
            })
            if len(results) >= top_k:
                break
        return results


vector_store = VectorStore()