"""
Distributed tracing with OpenTelemetry.
Tracks requests across multiple services.
"""
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from src.core.config import settings
from src.core.logging_config import app_logger


def setup_tracing(app):
    """
    Set up distributed tracing for the application.
    
    Traces:
    - API requests
    - Database queries
    - Redis operations
    - HTTP requests
    - LLM calls
    - Search operations
    """
    try:
        # Create resource
        resource = Resource(attributes={
            SERVICE_NAME: settings.app_name
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Create Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name="localhost",
            agent_port=6831,
        )
        
        # Add span processor
        processor = BatchSpanProcessor(jaeger_exporter)
        provider.add_span_processor(processor)
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        
        # Instrument frameworks
        FastAPIInstrumentor.instrument_app(app)
        SQLAlchemyInstrumentor().instrument()
        RedisInstrumentor().instrument()
        RequestsInstrumentor().instrument()
        
        app_logger.info("✅ Distributed tracing configured")
    
    except Exception as e:
        app_logger.error(f"❌ Failed to set up tracing: {e}")


def trace_operation(operation_name: str):
    """
    Decorator to trace custom operations.
    
    Usage:
        @trace_operation("embedding_generation")
        def generate_embedding(text):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            
            with tracer.start_as_current_span(operation_name) as span:
                # Add attributes
                span.set_attribute("function", func.__name__)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("status", "success")
                    return result
                
                except Exception as e:
                    span.set_attribute("status", "error")
                    span.set_attribute("error", str(e))
                    raise
        
        return wrapper
    return decorator


# Usage in code:
"""
from src.monitoring.tracing import trace_operation

@trace_operation("hybrid_search")
def hybrid_search(query, top_k):
    # Your search logic
    pass
"""