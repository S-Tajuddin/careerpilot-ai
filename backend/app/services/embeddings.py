"""
CareerPilot AI — Embedding Service
Generates and manages job embeddings using nomic-embed-text via Ollama.
Stores vectors in ChromaDB for semantic similarity search.
"""

import hashlib
import json
from typing import Optional

import httpx

from app.config import settings


class EmbeddingService:
    """
    Embedding service using nomic-embed-text (768 dimensions) via Ollama.
    Stores embeddings in ChromaDB for fast similarity search.
    """

    def __init__(self):
        self.ollama_host = settings.ollama_host
        self.model = settings.ollama_embedding_model
        self.dimensions = settings.embedding_dimensions
        self._chroma_client = None

    @property
    def chroma_client(self):
        """Lazy-init ChromaDB client."""
        if self._chroma_client is None:
            import chromadb
            self._chroma_client = chromadb.PersistentClient(
                path=str(settings.CHROMA_DIR),
            )
        return self._chroma_client

    @property
    def collection(self):
        """Get or create the jobs embedding collection."""
        return self.chroma_client.get_or_create_collection(
            name="jobs",
            metadata={"hnsw:space": "cosine"},
        )

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector using nomic-embed-text via Ollama."""
        if not text or not text.strip():
            return [0.0] * self.dimensions

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.ollama_host}/api/embeddings",
                    json={
                        "model": self.model,
                        "prompt": text[:8000],  # Truncate long texts
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("embedding", [0.0] * self.dimensions)
        except Exception as e:
            print(f"Embedding error: {e}")
            return [0.0] * self.dimensions

    def _make_doc_id(self, source: str, source_id: str) -> str:
        """Generate a deterministic document ID for ChromaDB."""
        raw = f"{source}:{source_id}"
        return hashlib.md5(raw.encode()).hexdigest()

    async def store_job_embedding(
        self,
        job_id: int,
        source: str,
        source_id: str,
        title: str,
        company_name: str,
        description: str,
        skills: list[str] = None,
    ) -> str:
        """
        Generate and store embedding for a job.
        Returns the ChromaDB document ID.
        """
        # Combine job info for embedding (weighted toward title + skills)
        skills_text = ", ".join(skills) if skills else ""
        embed_text = f"{title} at {company_name}. {skills_text}. {description[:2000]}"

        embedding = await self.generate_embedding(embed_text)

        doc_id = self._make_doc_id(source, source_id)

        # Store in ChromaDB
        try:
            self.collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[embed_text],
                metadatas=[{
                    "job_id": job_id,
                    "source": source,
                    "source_id": source_id,
                    "title": title[:200],
                    "company": company_name[:100],
                }],
            )
        except Exception as e:
            print(f"ChromaDB upsert error: {e}")

        return doc_id

    async def find_similar_jobs(
        self,
        query_text: str,
        n_results: int = 10,
        min_similarity: float = 0.5,
    ) -> list[dict]:
        """
        Find jobs similar to a query using embedding similarity.
        Returns list of {job_id, similarity, title, company}.
        """
        query_embedding = await self.generate_embedding(query_text)

        if all(v == 0.0 for v in query_embedding):
            return []

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, 50),
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            print(f"ChromaDB query error: {e}")
            return []

        similar = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i] if results["distances"] else 1.0
                # Cosine distance → similarity
                similarity = 1.0 - distance

                if similarity < min_similarity:
                    continue

                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                similar.append({
                    "doc_id": doc_id,
                    "job_id": metadata.get("job_id"),
                    "similarity": round(similarity, 4),
                    "title": metadata.get("title", ""),
                    "company": metadata.get("company", ""),
                })

        return similar

    async def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts."""
        import math

        emb1 = await self.generate_embedding(text1)
        emb2 = await self.generate_embedding(text2)

        # Cosine similarity
        dot = sum(a * b for a, b in zip(emb1, emb2))
        norm1 = math.sqrt(sum(a * a for a in emb1))
        norm2 = math.sqrt(sum(b * b for b in emb2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot / (norm1 * norm2)


# Singleton
embedding_service = EmbeddingService()
