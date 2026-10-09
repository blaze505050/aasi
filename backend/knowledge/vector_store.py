"""Vector index abstraction and FAISS-backed implementation with pure NumPy fallback."""

from __future__ import annotations

from abc import ABC, abstractmethod
import json
import os
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


class VectorIndex(ABC):
    """Abstract vector storage and similarity search interface."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        pass

    @property
    @abstractmethod
    def total_vectors(self) -> int:
        pass

    @abstractmethod
    def add(self, vectors: np.ndarray, metadata_list: List[Dict[str, Any]]):
        """Add dense vectors and their corresponding metadata records."""
        pass

    @abstractmethod
    def search(
        self, query_vector: np.ndarray, k: int = 5
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Search for the top-k most similar items. Returns list of (metadata, score)."""
        pass

    @abstractmethod
    def save(self, directory: str):
        """Persist index and metadata to disk."""
        pass

    @abstractmethod
    def load(self, directory: str):
        """Load index and metadata from disk."""
        pass


class NumpyVectorIndex(VectorIndex):
    """Pure NumPy vector index fallback utilizing normalized inner product (cosine similarity)."""

    def __init__(self, dimension: int = 384):
        self._dimension = dimension
        self._metadata: List[Dict[str, Any]] = []
        self._vectors: Optional[np.ndarray] = None

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def total_vectors(self) -> int:
        return len(self._metadata) if self._vectors is not None else 0

    def add(self, vectors: np.ndarray, metadata_list: List[Dict[str, Any]]):
        if len(vectors) == 0:
            return
        if vectors.shape[1] != self._dimension:
            raise ValueError(
                f"Vector dimension {vectors.shape[1]} does not match index dimension {self._dimension}"
            )
        if len(vectors) != len(metadata_list):
            raise ValueError("Number of vectors and metadata items must match")

        vecs = np.ascontiguousarray(vectors, dtype=np.float32)
        if self._vectors is None:
            self._vectors = vecs
        else:
            self._vectors = np.vstack([self._vectors, vecs])
        self._metadata.extend(metadata_list)

    def search(
        self, query_vector: np.ndarray, k: int = 5
    ) -> List[Tuple[Dict[str, Any], float]]:
        if self._vectors is None or len(self._metadata) == 0:
            return []

        q = np.ascontiguousarray(query_vector.reshape(-1), dtype=np.float32)
        sims = np.dot(self._vectors, q)
        top_k_indices = np.argsort(-sims)[: min(k, len(self._metadata))]

        results: List[Tuple[Dict[str, Any], float]] = []
        for idx in top_k_indices:
            results.append((self._metadata[idx], float(sims[idx])))
        return results

    def save(self, directory: str):
        os.makedirs(directory, exist_ok=True)
        if self._vectors is not None:
            np.save(os.path.join(directory, "vectors.npy"), self._vectors)
        with open(os.path.join(directory, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, indent=2, default=str)

    def load(self, directory: str):
        vec_file = os.path.join(directory, "vectors.npy")
        meta_file = os.path.join(directory, "metadata.json")

        if os.path.exists(vec_file):
            self._vectors = np.load(vec_file)
            self._dimension = self._vectors.shape[1]
        if os.path.exists(meta_file):
            with open(meta_file, "r", encoding="utf-8") as f:
                self._metadata = json.load(f)


class FAISSVectorIndex(VectorIndex):
    """FAISS-powered vector index with automatic pure NumPy fallback if faiss cannot be loaded."""

    def __init__(self, dimension: int = 384):
        self._dimension = dimension
        self._metadata: List[Dict[str, Any]] = []
        self._fallback: Optional[NumpyVectorIndex] = None
        try:
            import faiss
            self._faiss = faiss
            self._index = faiss.IndexFlatIP(dimension)
        except Exception:
            self._faiss = None
            self._index = None
            self._fallback = NumpyVectorIndex(dimension)

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def total_vectors(self) -> int:
        if self._fallback:
            return self._fallback.total_vectors
        return self._index.ntotal

    def add(self, vectors: np.ndarray, metadata_list: List[Dict[str, Any]]):
        if self._fallback:
            return self._fallback.add(vectors, metadata_list)

        if len(vectors) == 0:
            return
        if vectors.shape[1] != self._dimension:
            raise ValueError(
                f"Vector dimension {vectors.shape[1]} does not match index dimension {self._dimension}"
            )
        if len(vectors) != len(metadata_list):
            raise ValueError("Number of vectors and metadata items must match")

        vecs = np.ascontiguousarray(vectors, dtype=np.float32)
        self._index.add(vecs)
        self._metadata.extend(metadata_list)

    def search(
        self, query_vector: np.ndarray, k: int = 5
    ) -> List[Tuple[Dict[str, Any], float]]:
        if self._fallback:
            return self._fallback.search(query_vector, k)

        if self._index.ntotal == 0:
            return []

        q_vec = np.ascontiguousarray(
            query_vector.reshape(1, -1), dtype=np.float32
        )
        k = min(k, self._index.ntotal)
        scores, indices = self._index.search(q_vec, k)

        results: List[Tuple[Dict[str, Any], float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self._metadata):
                results.append((self._metadata[idx], float(score)))

        return results

    def save(self, directory: str):
        if self._fallback:
            return self._fallback.save(directory)

        os.makedirs(directory, exist_ok=True)
        index_file = os.path.join(directory, "faiss.index")
        meta_file = os.path.join(directory, "metadata.json")

        self._faiss.write_index(self._index, index_file)
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, indent=2, default=str)

    def load(self, directory: str):
        if self._fallback:
            return self._fallback.load(directory)

        index_file = os.path.join(directory, "faiss.index")
        meta_file = os.path.join(directory, "metadata.json")

        if not os.path.exists(index_file) or not os.path.exists(meta_file):
            raise FileNotFoundError(f"Index files not found in {directory}")

        self._index = self._faiss.read_index(index_file)
        with open(meta_file, "r", encoding="utf-8") as f:
            self._metadata = json.load(f)
        self._dimension = self._index.d
