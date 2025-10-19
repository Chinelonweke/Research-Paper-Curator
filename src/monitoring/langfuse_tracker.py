"""
Langfuse LLM Observability Tracker.
Monitors LLM calls, performance, costs, and quality metrics.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
from functools import wraps
import time
import json

try:
    from langfuse import Langfuse
    from langfuse.decorators import observe, langfuse_context
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    # Create dummy decorators if Langfuse not available
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])

from src.core.config import settings
from src.core.logging_config import app_logger


class LangfuseTracker:
    """
    Langfuse integration for LLM observability.
    
    Features:
    - Track all LLM calls
    - Monitor token usage and costs
    - Track retrieval quality
    - Log user feedback
    - Session management
    - Performance analytics
    """
    
    def __init__(
        self,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        host: Optional[str] = None
    ):
        """
        Initialize Langfuse tracker.
        
        Args:
            public_key: Langfuse public key
            secret_key: Langfuse secret key
            host: Langfuse host URL
        """
        self.enabled = LANGFUSE_AVAILABLE
        self.client: Optional[Langfuse] = None
        
        if not LANGFUSE_AVAILABLE:
            app_logger.warning("Langfuse not installed. Install with: pip install langfuse")
            return
        
        # Get credentials from settings or parameters
        self.public_key = public_key or getattr(settings, 'langfuse_public_key', None)
        self.secret_key = secret_key or getattr(settings, 'langfuse_secret_key', None)
        self.host = host or getattr(settings, 'langfuse_host', 'https://cloud.langfuse.com')
        
        if not self.public_key or not self.secret_key:
            app_logger.warning("Langfuse credentials not configured. Tracking disabled.")
            self.enabled = False
            return
        
        try:
            self.client = Langfuse(
                public_key=self.public_key,
                secret_key=self.secret_key,
                host=self.host
            )
            
            app_logger.info("✅ Langfuse tracking initialized")
            self.enabled = True
            
        except Exception as e:
            app_logger.error(f"Failed to initialize Langfuse: {e}")
            self.enabled = False
    
    def create_trace(
        self,
        name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Create a new trace for tracking a complete user interaction.
        
        Args:
            name: Trace name (e.g., "question_answering")
            user_id: User identifier
            session_id: Session identifier
            metadata: Additional metadata
            tags: Tags for categorization
        
        Returns:
            Trace ID or None if tracking disabled
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            trace = self.client.trace(
                name=name,
                user_id=user_id,
                session_id=session_id,
                metadata=metadata or {},
                tags=tags or []
            )
            
            return trace.id
        
        except Exception as e:
            app_logger.error(f"Error creating trace: {e}")
            return None
    
    def track_retrieval(
        self,
        trace_id: Optional[str],
        query: str,
        results: List[Dict[str, Any]],
        top_k: int,
        search_type: str = "hybrid",
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Track retrieval/search operation.
        
        Args:
            trace_id: Parent trace ID
            query: Search query
            results: Retrieved results
            top_k: Number of results requested
            search_type: Type of search (hybrid, semantic, keyword)
            duration_ms: Search duration in milliseconds
            metadata: Additional metadata
        
        Returns:
            Span ID or None
        """
        if not self.enabled or not self.client or not trace_id:
            return None
        
        try:
            # Extract key information from results
            result_ids = [r.get('arxiv_id', 'unknown') for r in results[:top_k]]
            scores = [r.get('hybrid_score', 0) for r in results[:top_k]]
            
            span_metadata = {
                "query": query,
                "top_k": top_k,
                "search_type": search_type,
                "results_count": len(results),
                "result_ids": result_ids,
                "scores": scores,
                "avg_score": sum(scores) / len(scores) if scores else 0,
                **(metadata or {})
            }
            
            span = self.client.span(
                trace_id=trace_id,
                name="retrieval",
                input={"query": query, "top_k": top_k},
                output={"results": result_ids, "count": len(results)},
                metadata=span_metadata,
                start_time=datetime.now() if not duration_ms else None,
                end_time=datetime.now() if duration_ms else None
            )
            
            return span.id
        
        except Exception as e:
            app_logger.error(f"Error tracking retrieval: {e}")
            return None
    
    def track_llm_call(
        self,
        trace_id: Optional[str],
        model: str,
        prompt: str,
        response: str,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        duration_ms: Optional[float] = None,
        temperature: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Track LLM generation call.
        
        Args:
            trace_id: Parent trace ID
            model: Model name (e.g., "llama2", "gpt-4")
            prompt: Input prompt
            response: Generated response
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            total_tokens: Total tokens used
            duration_ms: Generation duration in milliseconds
            temperature: Temperature parameter
            metadata: Additional metadata
        
        Returns:
            Generation ID or None
        """
        if not self.enabled or not self.client or not trace_id:
            return None
        
        try:
            usage = {}
            if prompt_tokens is not None:
                usage['prompt_tokens'] = prompt_tokens
            if completion_tokens is not None:
                usage['completion_tokens'] = completion_tokens
            if total_tokens is not None:
                usage['total_tokens'] = total_tokens
            
            generation_metadata = {
                "temperature": temperature,
                "model": model,
                **(metadata or {})
            }
            
            generation = self.client.generation(
                trace_id=trace_id,
                name="llm_generation",
                model=model,
                prompt=prompt,
                completion=response,
                usage=usage if usage else None,
                metadata=generation_metadata,
                start_time=datetime.now() if not duration_ms else None,
                end_time=datetime.now() if duration_ms else None
            )
            
            # Calculate and add cost if possible
            if total_tokens:
                cost = self._calculate_cost(model, prompt_tokens, completion_tokens)
                if cost:
                    generation.update(cost=cost)
            
            return generation.id
        
        except Exception as e:
            app_logger.error(f"Error tracking LLM call: {e}")
            return None
    
    def track_embedding_generation(
        self,
        trace_id: Optional[str],
        model: str,
        texts: List[str],
        embeddings_count: int,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Track embedding generation.
        
        Args:
            trace_id: Parent trace ID
            model: Embedding model name
            texts: Input texts
            embeddings_count: Number of embeddings generated
            duration_ms: Generation duration
            metadata: Additional metadata
        
        Returns:
            Span ID or None
        """
        if not self.enabled or not self.client or not trace_id:
            return None
        
        try:
            span_metadata = {
                "model": model,
                "texts_count": len(texts),
                "embeddings_count": embeddings_count,
                "avg_text_length": sum(len(t) for t in texts) / len(texts) if texts else 0,
                **(metadata or {})
            }
            
            span = self.client.span(
                trace_id=trace_id,
                name="embedding_generation",
                input={"texts_count": len(texts)},
                output={"embeddings_count": embeddings_count},
                metadata=span_metadata
            )
            
            return span.id
        
        except Exception as e:
            app_logger.error(f"Error tracking embedding generation: {e}")
            return None
    
    def track_reranking(
        self,
        trace_id: Optional[str],
        initial_results: List[Dict[str, Any]],
        reranked_results: List[Dict[str, Any]],
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Track result reranking operation.
        
        Args:
            trace_id: Parent trace ID
            initial_results: Results before reranking
            reranked_results: Results after reranking
            duration_ms: Reranking duration
            metadata: Additional metadata
        
        Returns:
            Span ID or None
        """
        if not self.enabled or not self.client or not trace_id:
            return None
        
        try:
            # Calculate ranking changes
            initial_ids = [r.get('arxiv_id') for r in initial_results]
            reranked_ids = [r.get('arxiv_id') for r in reranked_results]
            
            # Calculate how many positions each result moved
            position_changes = []
            for idx, doc_id in enumerate(reranked_ids):
                if doc_id in initial_ids:
                    old_pos = initial_ids.index(doc_id)
                    position_changes.append(abs(old_pos - idx))
            
            span_metadata = {
                "initial_count": len(initial_results),
                "reranked_count": len(reranked_results),
                "avg_position_change": sum(position_changes) / len(position_changes) if position_changes else 0,
                "max_position_change": max(position_changes) if position_changes else 0,
                **(metadata or {})
            }
            
            span = self.client.span(
                trace_id=trace_id,
                name="reranking",
                input={"initial_results": initial_ids},
                output={"reranked_results": reranked_ids},
                metadata=span_metadata
            )
            
            return span.id
        
        except Exception as e:
            app_logger.error(f"Error tracking reranking: {e}")
            return None
    
    def add_score(
        self,
        trace_id: str,
        name: str,
        value: float,
        comment: Optional[str] = None
    ):
        """
        Add a score/metric to a trace.
        
        Args:
            trace_id: Trace ID
            name: Score name (e.g., "relevance", "quality", "user_rating")
            value: Score value
            comment: Optional comment
        """
        if not self.enabled or not self.client:
            return
        
        try:
            self.client.score(
                trace_id=trace_id,
                name=name,
                value=value,
                comment=comment
            )
        
        except Exception as e:
            app_logger.error(f"Error adding score: {e}")
    
    def track_user_feedback(
        self,
        trace_id: str,
        rating: int,
        feedback_text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track user feedback on a response.
        
        Args:
            trace_id: Trace ID
            rating: User rating (e.g., 1-5 stars, thumbs up/down)
            feedback_text: Optional feedback text
            metadata: Additional metadata
        """
        if not self.enabled or not self.client:
            return
        
        try:
            # Add rating as score
            self.client.score(
                trace_id=trace_id,
                name="user_rating",
                value=rating,
                comment=feedback_text
            )
            
            # Add feedback as event
            if feedback_text or metadata:
                self.client.event(
                    trace_id=trace_id,
                    name="user_feedback",
                    metadata={
                        "rating": rating,
                        "feedback": feedback_text,
                        **(metadata or {})
                    }
                )
        
        except Exception as e:
            app_logger.error(f"Error tracking user feedback: {e}")
    
    def track_error(
        self,
        trace_id: str,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track an error that occurred during processing.
        
        Args:
            trace_id: Trace ID
            error_type: Type of error
            error_message: Error message
            stack_trace: Stack trace
            metadata: Additional metadata
        """
        if not self.enabled or not self.client:
            return
        
        try:
            self.client.event(
                trace_id=trace_id,
                name="error",
                metadata={
                    "error_type": error_type,
                    "error_message": error_message,
                    "stack_trace": stack_trace,
                    **(metadata or {})
                }
            )
        
        except Exception as e:
            app_logger.error(f"Error tracking error: {e}")
    
    def end_trace(
        self,
        trace_id: str,
        output: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        End a trace and record final output.
        
        Args:
            trace_id: Trace ID
            output: Final output data
            metadata: Final metadata
        """
        if not self.enabled or not self.client:
            return
        
        try:
            # Update trace with final output
            if output or metadata:
                self.client.trace(
                    id=trace_id,
                    output=output,
                    metadata=metadata
                )
        
        except Exception as e:
            app_logger.error(f"Error ending trace: {e}")
    
    def flush(self):
        """Flush pending events to Langfuse."""
        if self.enabled and self.client:
            try:
                self.client.flush()
            except Exception as e:
                app_logger.error(f"Error flushing Langfuse events: {e}")
    
    def _calculate_cost(
        self,
        model: str,
        prompt_tokens: Optional[int],
        completion_tokens: Optional[int]
    ) -> Optional[float]:
        """
        Calculate cost based on token usage.
        
        Args:
            model: Model name
            prompt_tokens: Prompt tokens
            completion_tokens: Completion tokens
        
        Returns:
            Cost in USD or None
        """
        if not prompt_tokens or not completion_tokens:
            return None
        
        # Pricing per 1K tokens (update as needed)
        pricing = {
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
            "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
            "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
            "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
            "claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125},
        }
        
        # Ollama models are free (self-hosted)
        if model.lower() in ["llama2", "mistral", "mixtral", "codellama"]:
            return 0.0
        
        if model not in pricing:
            return None
        
        prompt_cost = (prompt_tokens / 1000) * pricing[model]["prompt"]
        completion_cost = (completion_tokens / 1000) * pricing[model]["completion"]
        
        return prompt_cost + completion_cost


class TrackedRAGSession:
    """
    Context manager for tracked RAG sessions.
    Automatically creates and manages Langfuse traces.
    """
    
    def __init__(
        self,
        tracker: LangfuseTracker,
        session_name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ):
        """
        Initialize tracked session.
        
        Args:
            tracker: LangfuseTracker instance
            session_name: Name of the session
            user_id: User identifier
            session_id: Session identifier
            metadata: Session metadata
            tags: Session tags
        """
        self.tracker = tracker
        self.session_name = session_name
        self.user_id = user_id
        self.session_id = session_id or str(uuid.uuid4())
        self.metadata = metadata or {}
        self.tags = tags or []
        self.trace_id: Optional[str] = None
        self.start_time = None
    
    def __enter__(self):
        """Start the tracked session."""
        self.start_time = time.time()
        
        self.trace_id = self.tracker.create_trace(
            name=self.session_name,
            user_id=self.user_id,
            session_id=self.session_id,
            metadata=self.metadata,
            tags=self.tags
        )
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End the tracked session."""
        duration_ms = (time.time() - self.start_time) * 1000 if self.start_time else None
        
        if exc_type is not None:
            # An error occurred
            self.tracker.track_error(
                trace_id=self.trace_id,
                error_type=exc_type.__name__,
                error_message=str(exc_val),
                stack_trace=str(exc_tb)
            )
        
        # End trace
        self.tracker.end_trace(
            trace_id=self.trace_id,
            metadata={
                **self.metadata,
                "duration_ms": duration_ms,
                "success": exc_type is None
            }
        )
        
        # Flush events
        self.tracker.flush()
        
        return False  # Don't suppress exceptions


# Global tracker instance
_tracker: Optional[LangfuseTracker] = None


def get_langfuse_tracker() -> LangfuseTracker:
    """Get global Langfuse tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = LangfuseTracker()
    return _tracker


def track_rag_query(func):
    """
    Decorator to automatically track RAG queries with Langfuse.
    
    Usage:
        @track_rag_query
        def answer_question(question: str, top_k: int = 5):
            # Your RAG logic here
            return answer
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        tracker = get_langfuse_tracker()
        
        if not tracker.enabled:
            # If tracking disabled, just call the function
            return func(*args, **kwargs)
        
        # Extract question from arguments
        question = kwargs.get('question') or (args[0] if args else None)
        user_id = kwargs.get('user_id', 'anonymous')
        
        with TrackedRAGSession(
            tracker=tracker,
            session_name="rag_query",
            user_id=user_id,
            metadata={"function": func.__name__},
            tags=["rag", "question_answering"]
        ) as session:
            # Call the function
            result = func(*args, **kwargs)
            
            # Track the result
            if isinstance(result, dict) and 'answer' in result:
                session.tracker.add_score(
                    trace_id=session.trace_id,
                    name="response_generated",
                    value=1.0
                )
            
            return result
    
    return wrapper


# Example usage functions
def track_complete_rag_pipeline(
    tracker: LangfuseTracker,
    question: str,
    search_results: List[Dict[str, Any]],
    llm_response: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> Optional[str]:
    """
    Track a complete RAG pipeline execution.
    
    Args:
        tracker: LangfuseTracker instance
        question: User question
        search_results: Retrieved search results
        llm_response: Generated LLM response
        user_id: User identifier
        session_id: Session identifier
    
    Returns:
        Trace ID or None
    """
    # Create trace
    trace_id = tracker.create_trace(
        name="rag_pipeline",
        user_id=user_id,
        session_id=session_id,
        metadata={
            "question": question,
            "search_results_count": len(search_results)
        },
        tags=["rag", "production"]
    )
    
    if not trace_id:
        return None
    
    # Track retrieval
    tracker.track_retrieval(
        trace_id=trace_id,
        query=question,
        results=search_results,
        top_k=len(search_results),
        search_type="hybrid"
    )
    
    # Track LLM generation
    tracker.track_llm_call(
        trace_id=trace_id,
        model="llama2",
        prompt=question,
        response=llm_response,
        metadata={"num_retrieved_docs": len(search_results)}
    )
    
    # End trace
    tracker.end_trace(
        trace_id=trace_id,
        output={"answer": llm_response}
    )
    
    # Flush
    tracker.flush()
    
    return trace_id


if __name__ == "__main__":
    # Example usage
    tracker = LangfuseTracker()
    
    if tracker.enabled:
        # Example: Track a RAG query
        trace_id = tracker.create_trace(
            name="test_rag_query",
            user_id="test_user",
            metadata={"test": True}
        )
        
        # Track retrieval
        tracker.track_retrieval(
            trace_id=trace_id,
            query="What is machine learning?",
            results=[
                {"arxiv_id": "1234.5678", "hybrid_score": 0.95},
                {"arxiv_id": "8765.4321", "hybrid_score": 0.87}
            ],
            top_k=2,
            search_type="hybrid"
        )
        
        # Track LLM generation
        tracker.track_llm_call(
            trace_id=trace_id,
            model="llama2",
            prompt="What is machine learning?",
            response="Machine learning is a subset of artificial intelligence...",
            total_tokens=150
        )
        
        # Add score
        tracker.add_score(
            trace_id=trace_id,
            name="relevance",
            value=0.9
        )
        
        # End trace
        tracker.end_trace(trace_id=trace_id)
        
        # Flush
        tracker.flush()
        
        print("✅ Langfuse tracking example completed")
    else:
        print("❌ Langfuse tracking is disabled")