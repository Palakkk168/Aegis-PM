"""ChromaDB-backed vector memory."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, ClassVar
from uuid import uuid4

import chromadb

from config import get_settings


class VectorMemory:
    """Project-scoped ChromaDB memory."""

    _instances: ClassVar[dict[str, "VectorMemory"]] = {}

    def __init__(self, project_id: str) -> None:
        """Initialize a Chroma collection for a project."""
        settings = get_settings()
        self.project_id = project_id
        self.client = chromadb.PersistentClient(path=str(settings.chroma_path))
        self.collection = self.client.get_or_create_collection(name=f"aegis_{project_id}")

    @classmethod
    def for_project(cls, project_id: str) -> "VectorMemory":
        """Return a singleton memory instance per project."""
        if project_id not in cls._instances:
            cls._instances[project_id] = cls(project_id)
        return cls._instances[project_id]

    async def store(self, text: str, metadata: dict[str, Any]) -> dict[str, Any]:
        """Embed and store text with metadata."""
        item_id = metadata.get("id", f"memory-{uuid4().hex[:12]}")
        self.collection.add(ids=[item_id], documents=[text], metadatas=[metadata])
        return {"success": True, "id": item_id}

    async def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        """Retrieve the most relevant memory snippets."""
        result = self.collection.query(query_texts=[query], n_results=top_k)
        documents: Iterable[str] = result.get("documents", [[]])[0]
        return list(documents)
