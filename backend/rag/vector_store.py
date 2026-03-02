"""
Vector Store Module
Generates embeddings and provides similarity search using FAISS.
"""
import os
import json
import pickle
import numpy as np
from typing import List, Dict, Any, Tuple

# Try to use sentence-transformers for local embeddings, fallback to OpenAI
try:
    from sentence_transformers import SentenceTransformer
    _model = None
    USE_LOCAL_EMBEDDINGS = True
except ImportError:
    USE_LOCAL_EMBEDDINGS = False

try:
    import faiss
    USE_FAISS = True
except ImportError:
    USE_FAISS = False


VECTOR_STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "vector_store")


def get_local_model():
    global _model
    if _model is None:
        print("Loading sentence-transformer model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def generate_embeddings(texts: List[str]) -> np.ndarray:
    """Generate embeddings using local sentence-transformers (no API key needed)."""
    model = get_local_model()
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    return embeddings.astype(np.float32)


class VectorStore:
    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: np.ndarray = None
        self.index = None
        os.makedirs(VECTOR_STORE_PATH, exist_ok=True)

    def build_index(self, chunks: List[Dict[str, Any]]):
        """Build vector index from document chunks."""
        print(f"Building vector index for {len(chunks)} chunks...")
        self.chunks = chunks
        texts = [c["content"] for c in chunks]
        self.embeddings = generate_embeddings(texts)

        if USE_FAISS:
            dim = self.embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dim)
            self.index.add(self.embeddings)
        
        self.save()
        print("Vector index built and saved.")

    def save(self):
        """Persist vector store to disk."""
        with open(os.path.join(VECTOR_STORE_PATH, "chunks.json"), "w") as f:
            json.dump(self.chunks, f)
        np.save(os.path.join(VECTOR_STORE_PATH, "embeddings.npy"), self.embeddings)

    def load(self) -> bool:
        """Load vector store from disk. Returns True if successful."""
        chunks_path = os.path.join(VECTOR_STORE_PATH, "chunks.json")
        embeddings_path = os.path.join(VECTOR_STORE_PATH, "embeddings.npy")

        if not os.path.exists(chunks_path) or not os.path.exists(embeddings_path):
            return False

        with open(chunks_path, "r") as f:
            self.chunks = json.load(f)
        self.embeddings = np.load(embeddings_path)

        if USE_FAISS and len(self.chunks) > 0:
            dim = self.embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dim)
            self.index.add(self.embeddings)

        print(f"Loaded vector store with {len(self.chunks)} chunks.")
        return True

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """Search for most relevant chunks given a query."""
        if not self.chunks:
            return []

        query_embedding = generate_embeddings([query])[0]

        if USE_FAISS and self.index is not None:
            distances, indices = self.index.search(
                query_embedding.reshape(1, -1), min(top_k, len(self.chunks))
            )
            results = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx < len(self.chunks):
                    score = 1 / (1 + dist)  # Convert distance to similarity
                    results.append((self.chunks[idx], score))
            return results
        else:
            # Fallback: cosine similarity
            scores = []
            for i, chunk_emb in enumerate(self.embeddings):
                score = self.cosine_similarity(query_embedding, chunk_emb)
                scores.append((self.chunks[i], score))
            scores.sort(key=lambda x: x[1], reverse=True)
            return scores[:top_k]


# Singleton instance
_vector_store = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
        if not _vector_store.load():
            print("No existing vector store found. Run /api/documents/ingest to build index.")
    return _vector_store
