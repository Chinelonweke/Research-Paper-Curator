"""
AI Answer Generator using Groq
"""
import os
import logging
from groq import Groq

logger = logging.getLogger(__name__)

class AnswerGenerator:
    """Generate intelligent answers using Groq LLM"""
    
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-70b-versatile"  # Fast and smart
        logger.info("✅ Groq AI Answer Generator initialized")
    
    def generate_answer(self, question: str, papers: list) -> str:
        """
        Generate comprehensive answer from papers
        
        Args:
            question: User's question
            papers: List of paper dicts with title, abstract, url
            
        Returns:
            Formatted markdown answer
        """
        try:
            # Build context from papers
            context = "Research Papers:\n\n"
            for i, paper in enumerate(papers, 1):
                context += f"{i}. **{paper.get('title')}**\n"
                context += f"   Abstract: {paper.get('abstract', '')[:500]}...\n"
                context += f"   URL: {paper.get('url', '')}\n\n"
            
            # Create prompt
            prompt = f"""You are an expert AI researcher explaining concepts clearly.

Question: {question}

Based on these research papers, provide a comprehensive, educational answer:

{context}

Your answer should:
1. Start with a clear, intuitive explanation (like explaining to a smart student)
2. Break down the concept step-by-step with examples
3. Explain WHY it matters and the problem it solves
4. Include technical details where relevant
5. Use analogies and simple language
6. Format with headers (##), bullet points, and emphasis
7. At the end, cite the papers as "Research Sources" with links

DO NOT just summarize papers. Create an original, educational explanation that happens to be informed by the research.

Answer in markdown format."""

            # Call Groq
            logger.info("🤖 Generating AI answer...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            
            answer = response.choices[0].message.content
            
            logger.info(f"✅ Generated {len(answer)} char answer")
            
            return answer
            
        except Exception as e:
            logger.error(f"❌ Answer generation failed: {e}")
            raise

# Global instance
answer_generator = None

def get_answer_generator():
    global answer_generator
    if answer_generator is None:
        answer_generator = AnswerGenerator()
    return answer_generator
