"""
Text chunking for papers.
"""
from typing import List, Dict
from src.core.logging_config import app_logger


class TextChunker:
    """Chunk text into smaller pieces for processing."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None
    ):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Target size of each chunk (characters)
            chunk_overlap: Overlap between chunks
            separators: List of separators to split on
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Chunk text into smaller pieces.
        
        Args:
            text: Text to chunk
            metadata: Metadata to include with each chunk
            
        Returns:
            List of chunk dictionaries
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size
            
            # If not at the end, try to break at a separator
            if end < len(text):
                # Find the best separator within the window
                best_split = end
                for separator in self.separators:
                    split_pos = text.rfind(separator, start, end)
                    if split_pos != -1:
                        best_split = split_pos + len(separator)
                        break
                end = best_split
            
            # Extract chunk
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk = {
                    'text': chunk_text,
                    'chunk_index': chunk_index,
                    'start_char': start,
                    'end_char': end,
                }
                
                # Add metadata
                if metadata:
                    chunk.update(metadata)
                
                chunks.append(chunk)
                chunk_index += 1
            
            # Move start position with overlap
            start = end - self.chunk_overlap
        
        return chunks
    
    def chunk_paper(self, paper: Dict) -> List[Dict]:
        """
        Chunk a paper into pieces.
        
        Args:
            paper: Paper dictionary with title, abstract, etc.
            
        Returns:
            List of chunks with metadata
        """
        # Combine title and abstract as main text
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        
        full_text = f"{title}\n\n{abstract}"
        
        metadata = {
            'arxiv_id': paper.get('arxiv_id'),
            'title': title,
            'authors': paper.get('authors', []),
            'categories': paper.get('categories', []),
            'published_date': paper.get('published_date'),
        }
        
        chunks = self.chunk_text(full_text, metadata)
        
        app_logger.info(f"Chunked paper {paper.get('arxiv_id')} into {len(chunks)} chunks")
        return chunks


def chunk_papers_batch(papers: List[Dict], chunk_size: int = 1000) -> List[Dict]:
    """
    Chunk multiple papers.
    
    Args:
        papers: List of papers
        chunk_size: Size of chunks
        
    Returns:
        List of all chunks
    """
    chunker = TextChunker(chunk_size=chunk_size)
    all_chunks = []
    
    for paper in papers:
        chunks = chunker.chunk_paper(paper)
        all_chunks.extend(chunks)
    
    app_logger.info(f"✅ Created {len(all_chunks)} chunks from {len(papers)} papers")
    return all_chunks