"""
Core Configuration - Complete Settings
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://neondb_owner:npg_zqua53pIJGUP@ep-frosty-queen-ahy6nn7k-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"
    )
    
    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_enabled: bool = False
    
    # OpenSearch
    opensearch_host: str = "opensearch"
    opensearch_port: int = 9200
    opensearch_enabled: bool = False
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    environment: str = "production"
    
    # Logging - THIS WAS MISSING!
    log_level: str = "INFO"
    
    # LLM
    openai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    ollama_host: str = "http://localhost:11434"
    
    # ArXiv
    arxiv_max_results: int = 50
    arxiv_cache_enabled: bool = True
    
    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_staging(self) -> bool:
        return self.environment == "staging"
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

print(f"✓ Configuration loaded: {settings.environment}")
print(f"✓ Database: NeonDB")
print(f"✓ Log level: {settings.log_level}")

