"""
Application configuration with comprehensive settings.
Supports multiple environments and all Phase 2 features.
"""
from functools import lru_cache
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    model_config = {
        "extra": "ignore",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }
    
    # =========================================================================
    # APPLICATION
    # =========================================================================
    app_name: str = Field(default="Research Paper Curator", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(default="development", description="Environment: development, staging, production")
    debug: bool = Field(default=True, description="Debug mode")
    
    # =========================================================================
    # API SERVER
    # =========================================================================
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=4, description="Number of API workers")
    api_reload: bool = Field(default=False, description="Auto-reload on code changes")
    
    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:7860,http://localhost:8000",
        description="Comma-separated CORS origins"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute")
    rate_limit_search_per_minute: int = Field(default=20, description="Search rate limit per minute")
    rate_limit_burst: int = Field(default=10, description="Burst size for rate limiting")
    
    # Security
    secret_key: str = Field(default="change-this-in-production-INSECURE", description="Secret key for sessions")
    api_key_enabled: bool = Field(default=False, description="Enable API key authentication")
    api_key: Optional[str] = Field(default=None, description="API key for authentication")
    
    # =========================================================================
    # DATABASE - PostgreSQL
    # =========================================================================
    db_type: str = Field(default="postgresql", description="Database type: sqlite or postgresql")
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(default="research_papers", description="Database name")
    db_user: str = Field(default="postgres", description="Database user")
    db_password: str = Field(default="postgres", description="Database password")
    db_pool_size: int = Field(default=20, description="Connection pool size")
    db_max_overflow: int = Field(default=10, description="Max overflow connections")
    
    # Sharding
    db_sharding_enabled: bool = Field(default=False, description="Enable database sharding")
    db_shard_count: int = Field(default=3, description="Number of database shards")
    
    @property
    def database_url(self) -> str:
        """Get database URL."""
        if self.db_type == "sqlite":
            return "sqlite:///./research_papers.db"
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
    
    @property
    def database_url_async(self) -> str:
        """Get async database URL."""
        if self.db_type == "sqlite":
            return "sqlite+aiosqlite:///./research_papers.db"
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
    
    # =========================================================================
    # REDIS CACHE
    # =========================================================================
    redis_enabled: bool = Field(default=True, description="Enable Redis cache")
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    
    @property
    def redis_url(self) -> str:
        """Get Redis URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    # =========================================================================
    # OPENSEARCH
    # =========================================================================
    opensearch_enabled: bool = Field(default=False, description="Enable OpenSearch")
    opensearch_host: str = Field(default="localhost", description="OpenSearch host")
    opensearch_port: int = Field(default=9200, description="OpenSearch port")
    opensearch_index: str = Field(default="research_papers", description="OpenSearch index name")
    
    @property
    def opensearch_url(self) -> str:
        """Get OpenSearch URL."""
        return f"http://{self.opensearch_host}:{self.opensearch_port}"
    
    # =========================================================================
    # LLM - OLLAMA & GROQ
    # =========================================================================
    llm_provider: str = Field(default="groq", description="LLM provider: groq or ollama")
    
    # Groq
    groq_api_key: Optional[str] = Field(default=None, description="Groq API key")
    groq_model: str = Field(default="llama-3.3-70b-versatile", description="Groq model name")
    groq_timeout: int = Field(default=60, description="Groq API timeout")
    
    # Ollama
    ollama_enabled: bool = Field(default=False, description="Enable Ollama")
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama host URL")
    ollama_model: str = Field(default="llama2", description="Ollama model name")
    ollama_timeout: int = Field(default=120, description="Ollama timeout")
    
    # =========================================================================
    # EMBEDDINGS
    # =========================================================================
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Embedding model name")
    embedding_dimension: int = Field(default=384, description="Embedding dimension")
    embedding_batch_size: int = Field(default=32, description="Batch size for embeddings")
    embedding_cache_enabled: bool = Field(default=True, description="Cache embeddings")
    
    # =========================================================================
    # SEARCH & RETRIEVAL
    # =========================================================================
    search_top_k: int = Field(default=10, description="Default number of search results")
    search_min_score: float = Field(default=0.5, description="Minimum similarity score")
    search_cache_ttl: int = Field(default=3600, description="Search cache TTL")
    
    # Chunking
    chunk_size: int = Field(default=500, description="Chunk size in characters")
    chunk_overlap: int = Field(default=50, description="Chunk overlap")
    max_chunks_per_paper: int = Field(default=50, description="Max chunks per paper")
    
    # =========================================================================
    # MESSAGE QUEUE
    # =========================================================================
    # RabbitMQ
    rabbitmq_enabled: bool = Field(default=False, description="Enable RabbitMQ")
    rabbitmq_host: str = Field(default="localhost", description="RabbitMQ host")
    rabbitmq_port: int = Field(default=5672, description="RabbitMQ port")
    rabbitmq_user: str = Field(default="guest", description="RabbitMQ user")
    rabbitmq_password: str = Field(default="guest", description="RabbitMQ password")
    
    # Kafka
    kafka_enabled: bool = Field(default=False, description="Enable Kafka")
    kafka_bootstrap_servers: str = Field(default="localhost:9092", description="Kafka servers")
    
    # =========================================================================
    # CELERY WORKER
    # =========================================================================
    celery_broker_url: str = Field(default="redis://localhost:6379/0", description="Celery broker URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/0", description="Celery result backend")
    
    # =========================================================================
    # MONITORING
    # =========================================================================
    # Langfuse
    langfuse_enabled: bool = Field(default=False, description="Enable Langfuse tracing")
    langfuse_public_key: Optional[str] = Field(default=None, description="Langfuse public key")
    langfuse_secret_key: Optional[str] = Field(default=None, description="Langfuse secret key")
    langfuse_host: str = Field(default="https://cloud.langfuse.com", description="Langfuse host")
    
    # Prometheus
    prometheus_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    prometheus_port: int = Field(default=9090, description="Prometheus port")
    
    # Sentry
    sentry_enabled: bool = Field(default=False, description="Enable Sentry error tracking")
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN")
    
    # =========================================================================
    # GRADIO UI
    # =========================================================================
    gradio_server_name: str = Field(default="0.0.0.0", description="Gradio server host")
    gradio_server_port: int = Field(default=7860, description="Gradio server port")
    gradio_share: bool = Field(default=False, description="Enable Gradio sharing")
    gradio_auth_enabled: bool = Field(default=False, description="Enable Gradio authentication")
    gradio_username: str = Field(default="admin", description="Gradio username")
    gradio_password: str = Field(default="admin", description="Gradio password")
    
    # =========================================================================
    # AUDIO FEATURES
    # =========================================================================
    audio_enabled: bool = Field(default=False, description="Enable audio features")
    whisper_model_size: str = Field(default="base", description="Whisper model size")
    stt_model: str = Field(default="openai/whisper-base", description="Speech-to-text model")
    tts_model: str = Field(default="coqui/XTTS-v2", description="Text-to-speech model")
    
    # =========================================================================
    # LOGGING
    # =========================================================================
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="logs/app.log", description="Log file path")
    log_max_bytes: int = Field(default=10485760, description="Max log file size (10MB)")
    log_backup_count: int = Field(default=5, description="Number of log backups")
    log_format: str = Field(default="json", description="Log format: json or text")
    
    # =========================================================================
    # CDN
    # =========================================================================
    cdn_enabled: bool = Field(default=False, description="Enable CDN")
    cdn_provider: str = Field(default="cloudflare", description="CDN provider")
    cdn_url: Optional[str] = Field(default=None, description="CDN URL")
    
    # =========================================================================
    # AIRFLOW
    # =========================================================================
    airflow_enabled: bool = Field(default=False, description="Enable Airflow")
    airflow_home: str = Field(default="/opt/airflow", description="Airflow home directory")
    airflow_webserver_port: int = Field(default=8080, description="Airflow webserver port")
    
    # =========================================================================
    # PRODUCTION SETTINGS
    # =========================================================================
    ssl_enabled: bool = Field(default=False, description="Enable SSL")
    ssl_certfile: Optional[str] = Field(default=None, description="SSL certificate file")
    ssl_keyfile: Optional[str] = Field(default=None, description="SSL key file")
    
    load_balancer_enabled: bool = Field(default=False, description="Enable load balancer")
    
    # =========================================================================
    # VALIDATORS
    # =========================================================================
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed = ['development', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f'Environment must be one of {allowed}')
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v = v.upper()
        if v not in allowed:
            raise ValueError(f'Log level must be one of {allowed}')
        return v
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"
    
    @property
    def is_staging(self) -> bool:
        """Check if running in staging."""
        return self.environment == "staging"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()


# Global settings instance
settings = get_settings()


# Export for convenience
__all__ = ['settings', 'Settings', 'get_settings']