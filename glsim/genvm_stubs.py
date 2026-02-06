"""Stub modules for GenVM-only libraries.

When contracts run in glsim, they may import libraries that only exist
inside the GenVM WASM environment (e.g., genlayer_embeddings). These stubs
provide minimal implementations to allow contracts to load and basic
operations to work.
"""

from __future__ import annotations

import sys
import types
from dataclasses import dataclass, field
from typing import Any, Generic, List, TypeVar

T = TypeVar("T")


# ---------- genlayer_embeddings stub ----------

class _EuclideanDistanceSquared:
    __gl_allow_storage__ = True


@dataclass
class _VecDBEntry:
    embedding: Any
    value: Any


class _VecDB:
    """Minimal vector database stub.

    Supports insert and knn. knn returns entries sorted by L2 distance.
    """

    __gl_allow_storage__ = True

    def __class_getitem__(cls, params):
        # Support VecDB[float32, Literal[384], ValueType, DistMetric] syntax
        return cls

    def __init__(self):
        self._entries: List[_VecDBEntry] = []

    def insert(self, embedding: Any, value: Any) -> None:
        self._entries.append(_VecDBEntry(embedding=embedding, value=value))

    def knn(self, query: Any, k: int = 5):
        """Return k nearest neighbors by Euclidean distance."""
        import numpy as np

        if not self._entries:
            return []

        query_arr = np.asarray(query, dtype=np.float32)
        scored = []
        for entry in self._entries:
            emb = np.asarray(entry.embedding, dtype=np.float32)
            dist = float(np.sum((query_arr - emb) ** 2))
            scored.append((dist, entry))

        scored.sort(key=lambda x: x[0])
        return [e for _, e in scored[:k]]


class _SentenceTransformer:
    """Stub sentence transformer that returns zero vectors."""

    def __init__(self, model_name: str = ""):
        self._model_name = model_name
        self._dim = 384  # all-MiniLM-L6-v2 dimension

    def __call__(self, text: str) -> Any:
        import numpy as np
        # Return deterministic pseudo-embedding based on text hash
        import hashlib
        h = hashlib.sha256(text.encode()).digest()
        # Use hash bytes to seed a small array
        rng = [b / 255.0 for b in h]
        # Tile to fill 384 dims
        vec = (rng * (self._dim // len(rng) + 1))[:self._dim]
        return np.array(vec, dtype=np.float32)


def install_genvm_stubs() -> None:
    """Install stub modules for GenVM-only libraries into sys.modules."""
    # genlayer_embeddings
    mod = types.ModuleType("genlayer_embeddings")
    mod.VecDB = _VecDB
    mod.EuclideanDistanceSquared = _EuclideanDistanceSquared
    mod.SentenceTransformer = _SentenceTransformer
    sys.modules["genlayer_embeddings"] = mod


def uninstall_genvm_stubs() -> None:
    """Remove stub modules from sys.modules."""
    sys.modules.pop("genlayer_embeddings", None)
