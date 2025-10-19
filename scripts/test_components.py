"""
Test all system components.
Validates that all services are working correctly.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import check_db_connection
from src.retrieval.opensearch_client import get_opensearch_client
from src.cache.redis_cache import get_redis_cache
from src.embeddings.generator import get_embedding_generator
from src.llm.ollama_client import get_ollama_client
from src.core.logging_config import app_logger


def test_database():
    """Test database connection."""
    app_logger.info("Testing PostgreSQL connection...")
    try:
        if check_db_connection():
            app_logger.info("✓ PostgreSQL: HEALTHY")
            return True
        else:
            app_logger.error("✗ PostgreSQL: FAILED")
            return False
    except Exception as e:
        app_logger.error(f"✗ PostgreSQL: ERROR - {e}")
        return False


def test_redis():
    """Test Redis connection."""
    app_logger.info("Testing Redis connection...")
    try:
        cache = get_redis_cache()
        if cache.health_check():
            stats = cache.get_stats()
            app_logger.info(f"✓ Redis: HEALTHY - {stats.get('total_keys', 0)} keys")
            return True
        else:
            app_logger.error("✗ Redis: FAILED")
            return False
    except Exception as e:
        app_logger.error(f"✗ Redis: ERROR - {e}")
        return False


def test_opensearch():
    """Test OpenSearch connection."""
    app_logger.info("Testing OpenSearch connection...")
    try:
        os_client = get_opensearch_client()
        stats = os_client.get_index_stats()
        app_logger.info(f"✓ OpenSearch: HEALTHY - {stats.get('document_count', 0)} documents")
        return True
    except Exception as e:
        app_logger.error(f"✗ OpenSearch: ERROR - {e}")
        return False


def test_embeddings():
    """Test embedding generation."""
    app_logger.info("Testing embedding generation...")
    try:
        generator = get_embedding_generator()
        test_text = "This is a test sentence for embedding generation."
        embedding = generator.generate_embedding(test_text)
        
        if len(embedding) > 0:
            app_logger.info(f"✓ Embeddings: HEALTHY - Dimension: {len(embedding)}")
            return True
        else:
            app_logger.error("✗ Embeddings: FAILED")
            return False
    except Exception as e:
        app_logger.error(f"✗ Embeddings: ERROR - {e}")
        return False


def test_llm():
    """Test LLM connection."""
    app_logger.info("Testing Ollama LLM...")
    try:
        llm = get_ollama_client()
        if llm._check_connection():
            app_logger.info(f"✓ Ollama: HEALTHY - Model: {llm.model}")
            
            # Test generation
            response = llm.generate("Say hello!", temperature=0.1)
            if response:
                app_logger.info(f"  Generated: {response[:50]}...")
            
            return True
        else:
            app_logger.error("✗ Ollama: FAILED")
            return False
    except Exception as e:
        app_logger.error(f"✗ Ollama: ERROR - {e}")
        return False


def main():
    """Main test runner."""
    app_logger.info("=" * 60)
    app_logger.info("SYSTEM COMPONENT TESTS")
    app_logger.info("=" * 60)
    
    results = {
        "PostgreSQL": test_database(),
        "Redis": test_redis(),
        "OpenSearch": test_opensearch(),
        "Embeddings": test_embeddings(),
        "Ollama": test_llm()
    }
    
    app_logger.info("=" * 60)
    app_logger.info("TEST RESULTS SUMMARY")
    app_logger.info("=" * 60)
    
    for component, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        app_logger.info(f"{component:.<20} {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    app_logger.info("=" * 60)
    app_logger.info(f"TOTAL: {passed_tests}/{total_tests} tests passed")
    app_logger.info("=" * 60)
    
    if passed_tests == total_tests:
        print("\n🎉 All components are healthy!")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} component(s) failed. Check logs for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())