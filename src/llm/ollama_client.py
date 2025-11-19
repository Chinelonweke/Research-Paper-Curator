"""
Groq LLM Client (Replaces Ollama).
Fast cloud-based LLM inference using Groq API.
"""
from typing import Optional, Dict, Any, List
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential
from src.core.config import settings
from src.core.logging_config import app_logger


class OllamaClient:
    """
    Groq LLM Client (renamed from OllamaClient for compatibility).
    
    This replaces Ollama with Groq but keeps the same interface
    so existing code doesn't need to change.
    
    Features:
    - Fast cloud inference
    - Multiple model support
    - Temperature and token control
    - Retry logic for reliability
    - Error handling
    
    Available Models:
    - mixtral-8x7b-32768: Best quality (default)
    - llama-3.1-70b-versatile: Very good, versatile
    - llama-3.1-8b-instant: Fast, good quality
    - gemma2-9b-it: Fast, lightweight
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Initialize Groq client.
        
        Args:
            api_key: Groq API key (or from settings)
            model: Model name to use (or from settings)
            timeout: Request timeout in seconds
        """
        # Get API key from settings or parameter
        self.api_key = api_key or getattr(settings, 'groq_api_key', None)
        self.model = model or getattr(settings, 'groq_model', 'mixtral-8x7b-32768')
        self.timeout = timeout or getattr(settings, 'ollama_timeout', 120)
        
        if not self.api_key:
            error_msg = (
                "Groq API key not found. "
                "Set GROQ_API_KEY in your .env file. "
                "Get one free at: https://console.groq.com/keys"
            )
            app_logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        try:
            self.client = Groq(api_key=self.api_key)
            app_logger.info(f"✅ Groq client initialized - Model: {self.model}")
            
            # Test connection
            self._check_connection()
            
        except Exception as e:
            app_logger.error(f"❌ Failed to initialize Groq client: {e}")
            raise
    
    def _check_connection(self) -> bool:
        """Check if Groq API is accessible."""
        try:
            # Make a simple test call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
                temperature=0
            )
            
            if response.choices:
                app_logger.info(f"✅ Groq API connection successful")
                return True
            else:
                app_logger.warning(f"⚠️ Groq API response was empty")
                return False
                
        except Exception as e:
            error_str = str(e).lower()
            
            if "api key" in error_str or "authentication" in error_str:
                app_logger.error(
                    f"❌ Groq API key is invalid. "
                    f"Please check your GROQ_API_KEY in .env file. "
                    f"Get a new key at: https://console.groq.com/keys"
                )
            elif "rate limit" in error_str:
                app_logger.warning(
                    f"⚠️ Groq rate limit reached. Wait a moment and try again."
                )
            elif "model" in error_str:
                app_logger.error(
                    f"❌ Model '{self.model}' not found. "
                    f"Available models: mixtral-8x7b-32768, llama-3.1-70b-versatile, "
                    f"llama-3.1-8b-instant, gemma2-9b-it"
                )
            else:
                app_logger.error(f"❌ Groq connection error: {e}")
            
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """
        Generate text using Groq.
        
        Args:
            prompt: User prompt
            system: System prompt (instructions for the AI)
            temperature: Sampling temperature (0.0-2.0, lower = more focused)
            max_tokens: Maximum tokens to generate (default: 2000)
            stream: Whether to stream the response (not fully implemented)
        
        Returns:
            Generated text
        """
        try:
            # Build messages
            messages = []
            
            # Add system message if provided
            if system:
                messages.append({
                    "role": "system",
                    "content": system
                })
            
            # Add user message
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            app_logger.debug(f"Sending request to Groq: {prompt[:100]}...")
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or 2000,
                top_p=1,
                stream=False  # Streaming not fully implemented yet
            )
            
            # Extract generated text
            generated_text = response.choices[0].message.content
            
            # Log usage
            if hasattr(response, 'usage'):
                usage = response.usage
                app_logger.debug(
                    f"Generated {len(generated_text)} chars. "
                    f"Tokens - Prompt: {usage.prompt_tokens}, "
                    f"Completion: {usage.completion_tokens}, "
                    f"Total: {usage.total_tokens}"
                )
            else:
                app_logger.debug(f"Generated {len(generated_text)} characters")
            
            return generated_text
            
        except Exception as e:
            error_str = str(e).lower()
            
            if "rate limit" in error_str:
                app_logger.error(
                    f"❌ Groq rate limit exceeded. "
                    f"Free tier: 30 requests/minute, 6000 tokens/minute. "
                    f"Wait a moment and try again."
                )
            elif "context length" in error_str or "token" in error_str:
                app_logger.error(
                    f"❌ Input too long for model {self.model}. "
                    f"Try reducing the context or using a model with larger context window."
                )
            elif "api key" in error_str:
                app_logger.error(
                    f"❌ Invalid Groq API key. Check your .env file."
                )
            else:
                app_logger.error(f"❌ Groq generation error: {e}")
            
            raise
    
    def generate_with_context(
        self,
        question: str,
        context: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3
    ) -> str:
        """
        Generate answer given question and retrieved context.
        
        Args:
            question: User question
            context: List of context documents from retrieval
            system_prompt: System instructions for the AI
            temperature: Sampling temperature (0.3 = more focused)
        
        Returns:
            Generated answer
        """
        try:
            # Build context string from retrieved documents
            context_parts = []
            for i, doc in enumerate(context[:10]):  # Limit to top 10 to avoid token limits
                title = doc.get('paper_title', 'Unknown')
                content = doc.get('content', '')
                arxiv_id = doc.get('arxiv_id', '')
                
                context_parts.append(
                    f"[Document {i+1}]\n"
                    f"Title: {title}\n"
                    f"arXiv ID: {arxiv_id}\n"
                    f"Content: {content}\n"
                )
            
            context_str = "\n".join(context_parts)
            
            # Build the prompt
            prompt = f"""Context from research papers:

{context_str}

Question: {question}

Based on the context above, provide a detailed and accurate answer to the question. 
If you reference specific information, mention which document it came from.
If the context doesn't contain enough information to answer fully, acknowledge this.

Answer:"""
            
            # Default system prompt if not provided
            if not system_prompt:
                system_prompt = (
                    "You are a helpful AI research assistant that answers questions about academic papers. "
                    "Base your answers strictly on the provided context. "
                    "Be accurate, cite sources by document number, and acknowledge if information is insufficient. "
                    "Use clear, professional language suitable for researchers."
                )
            
            return self.generate(
                prompt=prompt,
                system=system_prompt,
                temperature=temperature,
                max_tokens=2000
            )
            
        except Exception as e:
            app_logger.error(f"Error generating answer with context: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        model_info = {
            "mixtral-8x7b-32768": {
                "name": "Mixtral 8x7B",
                "context_window": 32768,
                "description": "High quality, good for complex tasks",
                "provider": "Mistral AI"
            },
            "llama-3.1-70b-versatile": {
                "name": "Llama 3.1 70B",
                "context_window": 131072,
                "description": "Very capable, versatile model",
                "provider": "Meta"
            },
            "llama-3.1-8b-instant": {
                "name": "Llama 3.1 8B Instant",
                "context_window": 131072,
                "description": "Fast, good quality",
                "provider": "Meta"
            },
            "gemma2-9b-it": {
                "name": "Gemma 2 9B",
                "context_window": 8192,
                "description": "Fast, lightweight",
                "provider": "Google"
            }
        }
        
        return {
            "model": self.model,
            "provider": "Groq",
            "info": model_info.get(self.model, {"name": self.model, "description": "Unknown model"}),
            "api_status": "connected"
        }


# Global client instance (for backward compatibility)
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """
    Get or create global Groq client instance.
    
    Note: Function name kept as 'get_ollama_client' for backward compatibility,
    but it now returns a Groq client.
    """
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client


# Alias for clarity (optional - use this in new code)
def get_groq_client() -> OllamaClient:
    """Get or create global Groq client instance."""
    return get_ollama_client()


# Example usage
if __name__ == "__main__":
    """Test the Groq client."""
    
    print("🧪 Testing Groq Client...")
    print("=" * 50)
    
    try:
        # Initialize client
        client = OllamaClient()
        
        # Test 1: Simple generation
        print("\n📝 Test 1: Simple Question")
        print("-" * 50)
        response = client.generate(
            prompt="What is machine learning? Answer in 2 sentences.",
            temperature=0.7
        )
        print(f"Response: {response}")
        
        # Test 2: With context
        print("\n📝 Test 2: Question with Context")
        print("-" * 50)
        
        mock_context = [
            {
                "paper_title": "Introduction to Neural Networks",
                "arxiv_id": "1234.5678",
                "content": "Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes that process information."
            }
        ]
        
        answer = client.generate_with_context(
            question="What are neural networks?",
            context=mock_context,
            temperature=0.3
        )
        print(f"Answer: {answer}")
        
        # Test 3: Model info
        print("\n📝 Test 3: Model Information")
        print("-" * 50)
        info = client.get_model_info()
        print(f"Model: {info['model']}")
        print(f"Provider: {info['provider']}")
        print(f"Info: {info['info']}")
        
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your GROQ_API_KEY in .env file")
        print("2. Make sure you have internet connection")
        print("3. Verify your API key at: https://console.groq.com/keys")