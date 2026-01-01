"""
Paper Indexer - Full RAG indexing pipeline
Downloads PDFs, extracts text, chunks, generates embeddings, stores in pgvector
"""
import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from src.database.models import Paper, PaperChunk
from src.services.pdf_processor import get_pdf_processor
from src.embeddings.generator import get_embedding_generator
from src.ingestion.chunker import TextChunker

logger = logging.getLogger(__name__)


class PaperIndexer:
    """Orchestrate full paper indexing pipeline"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        self.pdf_processor = get_pdf_processor()
        self.embedding_generator = get_embedding_generator()
        self.chunker = TextChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    def index_paper(self, paper: Paper, db: Session, use_abstract_fallback: bool = True) -> int:
        """
        Index a single paper: download PDF, chunk, embed, store

        Args:
            paper: Paper model instance
            db: Database session
            use_abstract_fallback: If PDF fails, use abstract

        Returns:
            Number of chunks created
        """
        logger.info(f"Indexing paper {paper.id}: {paper.title[:50]}...")

        # Delete existing chunks
        self.delete_paper_chunks(paper.id, db)

        # Try to get full PDF text
        full_text = None
        if paper.pdf_url:
            full_text = self.pdf_processor.process_paper(paper.pdf_url)

        # Fallback to abstract if PDF fails
        if not full_text and use_abstract_fallback:
            logger.warning(f"PDF extraction failed for paper {paper.id}, using abstract")
            full_text = f"{paper.title}\n\n{paper.abstract}"

        if not full_text:
            logger.error(f"No text available for paper {paper.id}")
            return 0

        # Chunk the text
        chunks_data = self.chunker.chunk_text(full_text)

        if not chunks_data:
            logger.warning(f"No chunks created for paper {paper.id}")
            return 0

        logger.info(f"Created {len(chunks_data)} chunks for paper {paper.id}")

        # Generate embeddings for all chunks
        chunk_texts = [c['text'] for c in chunks_data]
        embeddings = self.embedding_generator.generate_embeddings(chunk_texts)

        # Store chunks with embeddings
        chunks_created = 0
        for i, (chunk_data, embedding) in enumerate(zip(chunks_data, embeddings)):
            try:
                chunk = PaperChunk(
                    paper_id=paper.id,
                    chunk_index=chunk_data['chunk_index'],
                    text=chunk_data['text'],
                    embedding=embedding.tolist(),  # Convert numpy to list for pgvector
                    start_char=chunk_data.get('start_char'),
                    end_char=chunk_data.get('end_char')
                )
                db.add(chunk)
                chunks_created += 1
            except Exception as e:
                logger.error(f"Failed to create chunk {i} for paper {paper.id}: {e}")

        # Mark paper as indexed
        paper.indexed = True
        db.commit()

        logger.info(f"Successfully indexed paper {paper.id} with {chunks_created} chunks")
        return chunks_created

    def index_all_papers(
        self,
        db: Session,
        batch_size: int = 10,
        only_unindexed: bool = True
    ) -> Dict:
        """
        Index all papers in database

        Args:
            db: Database session
            batch_size: Number of papers to process at once
            only_unindexed: Only index papers not yet indexed

        Returns:
            Statistics dict
        """
        query = db.query(Paper)
        if only_unindexed:
            query = query.filter(Paper.indexed == False)

        papers = query.all()
        total_papers = len(papers)

        logger.info(f"Starting indexing of {total_papers} papers")

        stats = {
            "total_papers": total_papers,
            "successful": 0,
            "failed": 0,
            "total_chunks": 0
        }

        for i, paper in enumerate(papers):
            try:
                logger.info(f"Processing paper {i+1}/{total_papers}")
                chunks_created = self.index_paper(paper, db)
                if chunks_created > 0:
                    stats["successful"] += 1
                    stats["total_chunks"] += chunks_created
                else:
                    stats["failed"] += 1
            except Exception as e:
                logger.error(f"Failed to index paper {paper.id}: {e}")
                stats["failed"] += 1
                db.rollback()

        logger.info(f"Indexing complete: {stats}")
        return stats

    def delete_paper_chunks(self, paper_id: int, db: Session) -> int:
        """
        Delete all chunks for a paper

        Args:
            paper_id: Paper ID
            db: Database session

        Returns:
            Number of chunks deleted
        """
        deleted = db.query(PaperChunk).filter(
            PaperChunk.paper_id == paper_id
        ).delete()
        db.commit()

        if deleted:
            logger.info(f"Deleted {deleted} chunks for paper {paper_id}")

        return deleted

    def get_indexing_status(self, db: Session) -> Dict:
        """
        Get indexing statistics

        Args:
            db: Database session

        Returns:
            Status dict
        """
        total_papers = db.query(Paper).count()
        indexed_papers = db.query(Paper).filter(Paper.indexed == True).count()
        total_chunks = db.query(PaperChunk).count()

        return {
            "total_papers": total_papers,
            "indexed_papers": indexed_papers,
            "unindexed_papers": total_papers - indexed_papers,
            "total_chunks": total_chunks,
            "avg_chunks_per_paper": round(total_chunks / indexed_papers, 1) if indexed_papers > 0 else 0
        }


# Global singleton
_paper_indexer = None


def get_paper_indexer() -> PaperIndexer:
    """Get or create paper indexer singleton"""
    global _paper_indexer
    if _paper_indexer is None:
        _paper_indexer = PaperIndexer()
    return _paper_indexer
