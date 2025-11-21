"""Celery worker for background job processing."""
import os
from celery import Celery
from src.core.logging_config import app_logger

# Get Redis URL from environment
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

# Initialize Celery
celery_app = Celery(
    "rag_worker",
    broker=f"{redis_url}/1",
    backend=f"{redis_url}/2"
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

@celery_app.task(bind=True, max_retries=3)
def process_paper_async(self, arxiv_id: str):
    """Process a paper in the background."""
    try:
        from src.ingestion.processor import get_paper_processor
        from src.ingestion.arxiv_fetcher import get_arxiv_fetcher
        
        app_logger.info(f"Background task: Processing paper {arxiv_id}")
        
        fetcher = get_arxiv_fetcher()
        papers = fetcher.fetch_by_ids([arxiv_id])
        
        if not papers:
            raise ValueError(f"Paper {arxiv_id} not found on arXiv")
        
        processor = get_paper_processor()
        result = processor.process_single_paper(papers[0])
        
        app_logger.info(f"Background task completed: {arxiv_id} - {result}")
        
        return {"status": "success", "arxiv_id": arxiv_id, "result": result}
        
    except Exception as exc:
        app_logger.error(f"Background task failed: {arxiv_id} - {exc}")
        raise self.retry(exc=exc, countdown=60)

@celery_app.task
def batch_process_papers(arxiv_ids: list):
    """Process multiple papers in batch."""
    from celery import group
    
    job = group(process_paper_async.s(arxiv_id) for arxiv_id in arxiv_ids)
    result = job.apply_async()
    
    return {"task_id": result.id, "count": len(arxiv_ids)}

@celery_app.task
def cleanup_old_cache():
    """Periodic task to clean up old cache entries."""
    from src.cache.redis_cache import get_redis_cache
    
    try:
        cache = get_redis_cache()
        count = cache.clear_pattern("cache:l2:*")
        app_logger.info(f"Cache cleanup: Removed {count} entries")
        return {"cleaned": count}
    except Exception as e:
        app_logger.error(f"Cache cleanup failed: {e}")
        raise

celery_app.conf.beat_schedule = {
    'cleanup-cache-every-hour': {
        'task': 'src.worker.celery_app.cleanup_old_cache',
        'schedule': 3600.0,
    },
}
