"""
Prompt templates for LLM generation.
Provides structured prompts for different tasks.
"""
from typing import List, Dict, Any


class PromptTemplates:
    """Collection of prompt templates."""
    
    @staticmethod
    def get_qa_system_prompt() -> str:
        """Get system prompt for Q&A tasks."""
        return """You are an AI research assistant specialized in analyzing and explaining academic papers.

Your responsibilities:
1. Answer questions accurately based on the provided research paper excerpts
2. Cite specific papers when making claims
3. Admit when information is not in the provided context
4. Explain complex concepts clearly
5. Maintain academic rigor while being accessible

Guidelines:
- Always reference which paper(s) you're drawing from
- If asked about something not in the context, clearly state that
- Use clear, structured responses
- Explain technical terms when necessary
- Be concise but comprehensive"""
    
    @staticmethod
    def build_qa_prompt(question: str, contexts: List[Dict[str, Any]]) -> str:
        """
        Build Q&A prompt with contexts.
        
        Args:
            question: User question
            contexts: List of context documents
        
        Returns:
            Formatted prompt
        """
        # Format context
        context_parts = []
        for i, ctx in enumerate(contexts, 1):
            part = f"""[Document {i}]
Title: {ctx.get('paper_title', 'Unknown')}
Authors: {', '.join(ctx.get('paper_authors', ['Unknown'])[:3])}
Excerpt: {ctx.get('content', '')}
---"""
            context_parts.append(part)
        
        context_str = "\n\n".join(context_parts)
        
        prompt = f"""Given the following research paper excerpts, answer the question below.

RESEARCH PAPER EXCERPTS:
{context_str}

QUESTION:
{question}

INSTRUCTIONS:
- Base your answer on the provided excerpts
- Cite which document(s) you reference (e.g., "According to Document 1...")
- If the excerpts don't contain enough information, say so clearly
- Provide a detailed, well-structured answer

ANSWER:"""
        
        return prompt
    
    @staticmethod
    def build_summarization_prompt(text: str, max_length: int = 150) -> str:
        """
        Build summarization prompt.
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length in words
        
        Returns:
            Formatted prompt
        """
        return f"""Summarize the following research paper abstract or excerpt in no more than {max_length} words.
Focus on the key contributions, methods, and findings.

TEXT:
{text}

SUMMARY:"""
    
    @staticmethod
    def build_comparison_prompt(papers: List[Dict[str, Any]], aspect: str) -> str:
        """
        Build comparison prompt for multiple papers.
        
        Args:
            papers: List of papers to compare
            aspect: Aspect to compare (e.g., "methods", "results")
        
        Returns:
            Formatted prompt
        """
        papers_text = "\n\n".join([
            f"Paper {i+1}: {p['title']}\n{p['abstract']}"
            for i, p in enumerate(papers)
        ])
        
        return f"""Compare the following research papers focusing on their {aspect}.

PAPERS:
{papers_text}

Provide a structured comparison highlighting:
1. Similarities
2. Differences
3. Relative strengths and weaknesses

COMPARISON:"""
    
    @staticmethod
    def build_extraction_prompt(text: str, entity_type: str) -> str:
        """
        Build information extraction prompt.
        
        Args:
            text: Text to extract from
            entity_type: Type of entities to extract (e.g., "methods", "datasets")
        
        Returns:
            Formatted prompt
        """
        return f"""Extract all {entity_type} mentioned in the following research text.
List them in a structured format.

TEXT:
{text}

EXTRACTED {entity_type.upper()}:"""