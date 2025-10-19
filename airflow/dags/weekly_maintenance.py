"""
Weekly maintenance DAG - Cleanup and optimization tasks.
Runs every Sunday at 3 AM.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.cache.redis_cache import get_redis_cache
from src.database.connection import get_db_context
from src.core.logging_config import app_logger


default_args = {
    'owner': 'rag-system',
    'depends_on_past': False,
    'email': ['admin@example.com'],
    'email_on_failure': True,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
}


def cleanup_old_cache(**context):
    """Clear old cached entries."""
    try:
        app_logger.info("Starting cache cleanup")
        
        cache = get_redis_cache()
        
        # Get cache stats before cleanup
        stats_before = cache.get_stats()
        app_logger.info(f"Cache stats before cleanup: {stats_before}")
        
        # Clear old search cache (keep LLM cache)
        count = cache.clear_pattern("search:*")
        
        # Get stats after cleanup
        stats_after = cache.get_stats()
        app_logger.info(f"Cache stats after cleanup: {stats_after}")
        
        app_logger.info(f"Cleared {count} cache entries")
        
        return {"cleared": count, "stats_before": stats_before, "stats_after": stats_after}
        
    except Exception as e:
        app_logger.error(f"Cache cleanup failed: {e}", exc_info=True)
        raise


def cleanup_old_logs(**context):
    """Clean up old search logs from database."""
    try:
        app_logger.info("Starting log cleanup")
        
        with get_db_context() as db:
            from src.database.models import SearchLog
            
            # Delete logs older than 90 days
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            
            deleted = db.query(SearchLog).filter(
                SearchLog.timestamp < cutoff_date
            ).delete()
            
            db.commit()
            
            app_logger.info(f"Deleted {deleted} old search logs")
            
            return {"deleted_logs": deleted}
            
    except Exception as e:
        app_logger.error(f"Log cleanup failed: {e}", exc_info=True)
        raise


def optimize_database(**context):
    """Run database optimization tasks."""
    try:
        app_logger.info("Starting database optimization")
        
        with get_db_context() as db:
            # Analyze tables for query optimization
            db.execute("ANALYZE papers")
            db.execute("ANALYZE chunks")
            db.execute("ANALYZE search_logs")
            
            # Vacuum to reclaim space (optional, can be slow)
            # db.execute("VACUUM ANALYZE")
            
            db.commit()
            
            app_logger.info("Database optimization completed")
            
            return {"status": "completed"}
            
    except Exception as e:
        app_logger.error(f"Database optimization failed: {e}", exc_info=True)
        raise


def generate_weekly_stats(**context):
    """Generate weekly statistics report."""
    try:
        app_logger.info("Generating weekly statistics")
        
        with get_db_context() as db:
            from src.database.models import Paper, SearchLog
            from sqlalchemy import func
            
            # Papers added this week
            week_ago = datetime.utcnow() - timedelta(days=7)
            new_papers = db.query(Paper).filter(
                Paper.created_at >= week_ago
            ).count()
            
            # Search statistics
            total_searches = db.query(SearchLog).filter(
                SearchLog.timestamp >= week_ago
            ).count()
            
            avg_processing_time = db.query(
                func.avg(SearchLog.processing_time_ms)
            ).filter(
                SearchLog.timestamp >= week_ago
            ).scalar()
            
            # Popular queries
            from src.database.operations import SearchLogOperations
            popular = SearchLogOperations.get_popular_queries(db, limit=10, days=7)
            
            stats = {
                "new_papers_this_week": new_papers,
                "total_searches": total_searches,
                "avg_processing_time_ms": float(avg_processing_time) if avg_processing_time else 0,
                "popular_queries": popular
            }
            
            app_logger.info(f"Weekly stats: {stats}")
            
            context['task_instance'].xcom_push(key='weekly_stats', value=stats)
            
            return stats
            
    except Exception as e:
        app_logger.error(f"Stats generation failed: {e}", exc_info=True)
        raise


# Define the DAG
dag = DAG(
    'weekly_maintenance',
    default_args=default_args,
    description='Weekly maintenance and cleanup tasks',
    schedule_interval='0 3 * * 0',  # 3 AM every Sunday
    start_date=days_ago(1),
    catchup=False,
    tags=['maintenance', 'weekly', 'cleanup'],
)


# Define tasks
cache_cleanup_task = PythonOperator(
    task_id='cleanup_cache',
    python_callable=cleanup_old_cache,
    provide_context=True,
    dag=dag,
)

logs_cleanup_task = PythonOperator(
    task_id='cleanup_logs',
    python_callable=cleanup_old_logs,
    provide_context=True,
    dag=dag,
)

db_optimize_task = PythonOperator(
    task_id='optimize_database',
    python_callable=optimize_database,
    provide_context=True,
    dag=dag,
)

stats_task = PythonOperator(
    task_id='generate_stats',
    python_callable=generate_weekly_stats,
    provide_context=True,
    dag=dag,
)


# Define task dependencies
[cache_cleanup_task, logs_cleanup_task] >> db_optimize_task >> stats_task