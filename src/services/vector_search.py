"""
Vector Search Service - Semantic search using pgvector
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.embeddings.generator import get_embedding_generator
from src.database.models import PaperChunk, Paper

logger = logging.getLogger(__name__)


@dataclass
class ChunkResult:
    """Search result with chunk and metadata"""
    chunk_id: int
    paper_id: int
    paper_title: str
    paper_url: str
    chunk_index: int
    text: str
    similarity: float


class VectorSearch:
    """Semantic search using pgvector"""

    def __init__(self):
        self.embedding_generator = get_embedding_generator()

    def search(
        self,
        query: str,
        db: Session,
        limit: int = 5,
        similarity_threshold: float = 0.3
    ) -> List[ChunkResult]:
        """
        Search for relevant chunks using vector similarity

        Args:
            query: User's search query
            db: Database session
            limit: Maximum results to return
            similarity_threshold: Minimum similarity score

        Returns:
            List of ChunkResult objects
        """
        logger.info(f"Vector search for: {query[:50]}...")

        # Generate query embedding
        query_embedding = self.embedding_generator.generate_query_embedding(query)
        embedding_list = query_embedding.tolist()

        # pgvector cosine distance query
        # Note: <=> is cosine distance (1 - similarity), so we use 1 - distance for similarity
        sql = text("""
            SELECT
                pc.id as chunk_id,
                pc.paper_id,
                pc.chunk_index,
                pc.text,
                p.title as paper_title,
                p.pdf_url as paper_url,
                1 - (pc.embedding <=> :embedding) as similarity
            FROM paper_chunks pc
            JOIN papers p ON pc.paper_id = p.id
            WHERE pc.embedding IS NOT NULL
            ORDER BY pc.embedding <=> :embedding
            LIMIT :limit
        """)

        try:
            result = db.execute(
                sql,
                {"embedding": str(embedding_list), "limit": limit}
            )
            rows = result.fetchall()

            results = []
            for row in rows:
                similarity = float(row.similarity) if row.similarity else 0
                if similarity >= similarity_threshold:
                    results.append(ChunkResult(
                        chunk_id=row.chunk_id,
                        paper_id=row.paper_id,
                        paper_title=row.paper_title,
                        paper_url=row.paper_url or "",
                        chunk_index=row.chunk_index,
                        text=row.text,
                        similarity=similarity
                    ))

            logger.info(f"Found {len(results)} relevant chunks")
            return results

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    def search_by_paper(
        self,
        query: str,
        paper_id: int,
        db: Session,
        limit: int = 3
    ) -> List[ChunkResult]:
        """
        Search within a specific paper

        Args:
            query: Search query
            paper_id: Paper ID to search within
            db: Database session
            limit: Maximum results

        Returns:
            List of ChunkResult objects
        """
        logger.info(f"Searching within paper {paper_id}: {query[:30]}...")

        query_embedding = self.embedding_generator.generate_query_embedding(query)
        embedding_list = query_embedding.tolist()

        sql = text("""
            SELECT
                pc.id as chunk_id,
                pc.paper_id,
                pc.chunk_index,
                pc.text,
                p.title as paper_title,
                p.pdf_url as paper_url,
                1 - (pc.embedding <=> :embedding) as similarity
            FROM paper_chunks pc
            JOIN papers p ON pc.paper_id = p.id
            WHERE pc.paper_id = :paper_id
            AND pc.embedding IS NOT NULL
            ORDER BY pc.embedding <=> :embedding
            LIMIT :limit
        """)

        try:
            result = db.execute(
                sql,
                {"embedding": str(embedding_list), "paper_id": paper_id, "limit": limit}
            )
            rows = result.fetchall()

            results = [
                ChunkResult(
                    chunk_id=row.chunk_id,
                    paper_id=row.paper_id,
                    paper_title=row.paper_title,
                    paper_url=row.paper_url or "",
                    chunk_index=row.chunk_index,
                    text=row.text,
                    similarity=float(row.similarity) if row.similarity else 0
                )
                for row in rows
            ]

            return results

        except Exception as e:
            logger.error(f"Paper search failed: {e}")
            return []

    def get_context_for_question(
        self,
        question: str,
        db: Session,
        max_chunks: int = 5,
        max_context_length: int = 8000
    ) -> tuple[str, List[Dict]]:
        """
        Get context string for LLM from relevant chunks

        Args:
            question: User's question
            db: Database session
            max_chunks: Maximum chunks to include
            max_context_length: Maximum total context length

        Returns:
            Tuple of (context_string, sources_list)
        """
        chunks = self.search(question, db, limit=max_chunks)

        if not chunks:
            return "", []

        context_parts = []
        sources = []
        current_length = 0

        for chunk in chunks:
            chunk_text = f"[From: {chunk.paper_title}]\n{chunk.text}\n"

            if current_length + len(chunk_text) > max_context_length:
                break

            context_parts.append(chunk_text)
            current_length += len(chunk_text)

            # Track unique sources
            source = {
                "title": chunk.paper_title,
                "url": chunk.paper_url,
                "similarity": round(chunk.similarity, 3)
            }
            if source not in sources:
                sources.append(source)

        context = "\n---\n".join(context_parts)

        logger.info(f"Built context with {len(context_parts)} chunks, {len(sources)} sources")
        return context, sources


# Global singleton
_vector_search = None


def get_vector_search() -> VectorSearch:
    """Get or create vector search singleton"""
    global _vector_search
    if _vector_search is None:
        _vector_search = VectorSearch()
    return _vector_search
