"""
Celery worker for background job processing.
Handles long-running tasks asynchronously.
"""
from celery import Celery
from src.core.config import settings
from src.core.logging_config import app_logger

# Initialize Celery
celery_app = Celery(
    "rag_worker",
    broker=f"redis://{settings.redis_host}:{settings.redis_port}/1",
    backend=f"redis://{settings.redis_host}:{settings.redis_port}/2"
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)


@celery_app.task(bind=True, max_retries=3)
def process_paper_async(self, arxiv_id: str):
    """
    Process a paper in the background.
    
    Args:
        arxiv_id: arXiv ID of paper to process
    
    Returns:
        Processing status
    """
    try:
        from src.ingestion.processor import get_paper_processor
        from src.ingestion.arxiv_fetcher import get_arxiv_fetcher
        
        app_logger.info(f"Background task: Processing paper {arxiv_id}")
        
        # Fetch paper
        fetcher = get_arxiv_fetcher()
        papers = fetcher.fetch_by_ids([arxiv_id])
        
        if not papers:
            raise ValueError(f"Paper {arxiv_id} not found on arXiv")
        
        # Process paper
        processor = get_paper_processor()
        result = processor.process_single_paper(papers[0])
        
        app_logger.info(f"Background task completed: {arxiv_id} - {result}")
        
        return {"status": "success", "arxiv_id": arxiv_id, "result": result}
        
    except Exception as exc:
        app_logger.error(f"Background task failed: {arxiv_id} - {exc}")
        raise self.retry(exc=exc, countdown=60)  # Retry after 1 minute


@celery_app.task
def batch_process_papers(arxiv_ids: list):
    """
    Process multiple papers in batch.
    
    Args:
        arxiv_ids: List of arXiv IDs
    """
    from celery import group
    
    # Create group of parallel tasks
    job = group(process_paper_async.s(arxiv_id) for arxiv_id in arxiv_ids)
    result = job.apply_async()
    
    return {"task_id": result.id, "count": len(arxiv_ids)}


@celery_app.task
def cleanup_old_cache():
    """Periodic task to clean up old cache entries."""
    from src.cache.redis_cache import get_redis_cache
    
    try:
        cache = get_redis_cache()
        # Clear old entries
        count = cache.clear_pattern("cache:l2:*")
        app_logger.info(f"Cache cleanup: Removed {count} entries")
        return {"cleaned": count}
    except Exception as e:
        app_logger.error(f"Cache cleanup failed: {e}")
        raise


# Periodic tasks
celery_app.conf.beat_schedule = {
    'cleanup-cache-every-hour': {
        'task': 'src.worker.celery_app.cleanup_old_cache',
        'schedule': 3600.0,  # Every hour
    },
}