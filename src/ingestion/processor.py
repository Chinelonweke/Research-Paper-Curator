"""
Process and ingest papers into the database.
FIXED: Stores authors/categories as comma-separated strings to avoid PostgreSQL array literal issues.
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import json
import traceback

from src.database.models import Paper, Chunk
from src.database.operations import PaperOperations
from src.embeddings.generator import get_embedding_generator
from src.ingestion.arxiv_fetcher import ArxivFetcher
from src.ingestion.chunker import TextChunker
from src.core.logging_config import app_logger


class PaperProcessor:
    """Process and ingest papers into database."""
    
    def __init__(self, db: Session):
        """Initialize processor."""
        self.db = db
        self.fetcher = ArxivFetcher()
        self.chunker = TextChunker()
        self.embedding_gen = get_embedding_generator()
    
    def process_paper(self, paper_data: Dict) -> Optional[Paper]:
        """Process a single paper with extensive error handling."""
        arxiv_id = "unknown"
        
        try:
            # Step 1: Extract arxiv_id
            arxiv_id = paper_data.get('arxiv_id', 'unknown')
            app_logger.info(f"Processing paper: {arxiv_id}")
            
            # Step 2: Check if exists
            existing = PaperOperations.get_paper_by_arxiv_id(self.db, arxiv_id)
            if existing:
                app_logger.info(f"Paper {arxiv_id} already exists, skipping")
                return existing
            
            # Step 3: Prepare data - FIXED FOR POSTGRESQL
            app_logger.debug(f"Preparing data for {arxiv_id}")
            
            authors = paper_data.get('authors', [])
            categories = paper_data.get('categories', [])
            
            # Store as comma-separated strings to avoid PostgreSQL array literal issues
            if isinstance(authors, list):
                authors_str = ', '.join(authors)  # Simple comma-separated
            else:
                authors_str = str(authors)
            
            if isinstance(categories, list):
                categories_str = ', '.join(categories)  # Simple comma-separated
            else:
                categories_str = str(categories)
            
            # Step 4: Create Paper object
            app_logger.debug(f"Creating Paper object for {arxiv_id}")
            
            paper = Paper(
                arxiv_id=str(arxiv_id),
                title=str(paper_data.get('title', '')),
                abstract=str(paper_data.get('abstract', '')),
                authors=authors_str,
                categories=categories_str,
                primary_category=str(paper_data.get('primary_category', '')),
                published_date=paper_data.get('published_date'),
                updated_date=paper_data.get('updated_date'),
                pdf_url=str(paper_data.get('pdf_url', '')),
                comment=paper_data.get('comment'),
                journal_ref=paper_data.get('journal_ref'),
                doi=paper_data.get('doi'),
                indexed=datetime.utcnow()
            )
            
            # Step 5: Add and flush
            app_logger.debug(f"Adding paper {arxiv_id} to database")
            self.db.add(paper)
            self.db.flush()
            app_logger.debug(f"Paper {arxiv_id} flushed, got ID: {paper.id}")
            
            # Step 6: Create chunks
            app_logger.debug(f"Creating chunks for {arxiv_id}")
            chunks = self.chunker.chunk_paper(paper_data)
            app_logger.debug(f"Created {len(chunks)} chunks for {arxiv_id}")
            
            if not chunks:
                app_logger.warning(f"No chunks for {arxiv_id}, committing paper only")
                self.db.commit()
                return paper
            
            # Step 7: Generate embeddings
            app_logger.debug(f"Generating embeddings for {len(chunks)} chunks")
            chunk_texts = [c['text'] for c in chunks]
            embeddings = self.embedding_gen.generate_embeddings(chunk_texts)
            app_logger.debug(f"Generated {len(embeddings)} embeddings")
            
            # Step 8: Create chunks with embeddings ONE BY ONE
            for idx, (chunk_data, embedding) in enumerate(zip(chunks, embeddings)):
                try:
                    app_logger.debug(f"Creating chunk {idx+1}/{len(chunks)}")
                    
                    # Convert embedding to JSON string
                    import numpy as np
                    if isinstance(embedding, np.ndarray):
                        embedding_json = json.dumps(embedding.tolist())
                    else:
                        embedding_json = json.dumps(embedding)
                    
                    chunk = Chunk(
                        paper_id=paper.id,
                        chunk_index=chunk_data['chunk_index'],
                        text=chunk_data['text'],
                        start_char=chunk_data.get('start_char', 0),
                        end_char=chunk_data.get('end_char', len(chunk_data['text'])),
                        embedding=embedding_json
                    )
                    
                    self.db.add(chunk)
                    
                    # Flush every 10 chunks to avoid huge transactions
                    if (idx + 1) % 10 == 0:
                        self.db.flush()
                        app_logger.debug(f"Flushed {idx+1} chunks")
                    
                except Exception as chunk_error:
                    app_logger.error(f"Error creating chunk {idx}: {chunk_error}")
                    raise
            
            # Step 9: Final commit
            app_logger.debug(f"Committing all changes for {arxiv_id}")
            self.db.commit()
            
            app_logger.info(f"✅ Successfully processed {arxiv_id} with {len(chunks)} chunks")
            return paper
            
        except Exception as e:
            self.db.rollback()
            error_msg = f"Error processing {arxiv_id}: {str(e)}"
            app_logger.error(error_msg)
            app_logger.error(f"Full traceback: {traceback.format_exc()}")
            print(f"❌ {error_msg}")
            return None
    
    def process_papers_batch(self, papers_data: List[Dict]) -> int:
        """Process multiple papers."""
        processed = 0
        failed = 0
        total = len(papers_data)
        
        print(f"\nProcessing {total} papers...\n")
        
        for i, paper_data in enumerate(papers_data, 1):
            arxiv_id = paper_data.get('arxiv_id', 'unknown')
            print(f"[{i}/{total}] Processing: {arxiv_id}")
            
            result = self.process_paper(paper_data)
            if result:
                processed += 1
                print(f"    ✅ Success")
            else:
                failed += 1
                print(f"    ❌ Failed")
            
            # Progress update every 10 papers
            if i % 10 == 0:
                print(f"\n--- Progress: {i}/{total} ({processed} success, {failed} failed) ---\n")
        
        print(f"\n{'='*60}")
        print(f"Final Results:")
        print(f"  ✅ Processed: {processed}")
        print(f"  ❌ Failed: {failed}")
        print(f"  📊 Total: {total}")
        print(f"{'='*60}\n")
        
        app_logger.info(f"Batch complete: {processed} success, {failed} failed out of {total}")
        return processed
    
    def ingest_from_arxiv(
        self,
        categories: List[str] = None,
        max_per_category: int = 50
    ) -> int:
        """Fetch and ingest papers from arXiv."""
        if categories is None:
            categories = ["cs.AI", "cs.LG", "cs.CL"]
        
        print(f"\nFetching papers from arXiv...")
        print(f"Categories: {categories}")
        print(f"Max per category: {max_per_category}\n")
        
        app_logger.info(f"Starting arXiv ingestion for categories: {categories}")
        
        all_papers = []
        for category in categories:
            print(f"Fetching from {category}...")
            papers = self.fetcher.fetch_by_category(category, max_per_category)
            all_papers.extend(papers)
            print(f"  Got {len(papers)} papers from {category}")
        
        # Remove duplicates
        seen = set()
        unique_papers = []
        for paper in all_papers:
            paper_id = paper.get('arxiv_id')
            if paper_id and paper_id not in seen:
                seen.add(paper_id)
                unique_papers.append(paper)
        
        print(f"\nTotal unique papers: {len(unique_papers)}")
        
        # Process papers
        processed = self.process_papers_batch(unique_papers)
        
        app_logger.info(f"✅ Ingestion complete: {processed} papers added")
        return processed