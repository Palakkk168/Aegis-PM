"""Local lexical vector memory implementation."""

from __future__ import annotations

import asyncio
from collections import Counter
import json
import math
from pathlib import Path
import re


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]+")


class VectorStore:
    """Store and retrieve contextual memory using cosine similarity."""

    def __init__(self, path: Path) -> None:
        """Create a vector store backed by JSON."""
        self.path = path
        self._lock = asyncio.Lock()
        if not self.path.exists():
            self._persist([])

    async def store(self, entry_id: str, text: str, metadata: dict | None = None) -> None:
        """Store a memory entry."""
        async with self._lock:
            entries = self._load()
            tokens = Counter(self._tokenize(text))
            entries.append(
                {
                    "entry_id": entry_id,
                    "text": text,
                    "metadata": metadata or {},
                    "tokens": dict(tokens),
                }
            )
            self._persist(entries)

    async def retrieve(self, query: str, limit: int = 5) -> list[dict]:
        """Retrieve the most similar memory entries."""
        async with self._lock:
            entries = self._load()
            query_vector = Counter(self._tokenize(query))
            scored = []
            for entry in entries:
                score = self._cosine_similarity(query_vector, Counter(entry["tokens"]))
                if score > 0:
                    scored.append({**entry, "score": round(score, 4)})
            scored.sort(key=lambda item: item["score"], reverse=True)
            return scored[:limit]

    def _tokenize(self, text: str) -> list[str]:
        """Convert text into normalized lexical tokens."""
        return [token.lower() for token in TOKEN_PATTERN.findall(text)]

    def _cosine_similarity(self, left: Counter, right: Counter) -> float:
        """Compute cosine similarity between sparse term vectors."""
        intersection = set(left) & set(right)
        numerator = sum(left[token] * right[token] for token in intersection)
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        if not left_norm or not right_norm:
            return 0.0
        return numerator / (left_norm * right_norm)

    def _load(self) -> list[dict]:
        """Read all entries from disk."""
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _persist(self, entries: list[dict]) -> None:
        """Write entries to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
