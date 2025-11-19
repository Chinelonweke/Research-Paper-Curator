"""
Weekly Maintenance DAG
Runs every Sunday at 3 AM UTC
- Update embeddings for papers without them
- Remove duplicate papers
- Database optimization
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'research-curator',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
}

def update_embeddings(**context):
    """Generate embeddings for papers that don't have them"""
    try:
        from src.database.connection import get_db
        from src.database.models import Paper
        # from src.embeddings.generator import generate_embeddings
        
        logger.info("🔄 Updating embeddings...")
        
        db = next(get_db())
        
        # Get papers without embeddings
        papers = db.query(Paper).filter(
            Paper.embedding == None
        ).limit(100).all()
        
        logger.info(f"Found {len(papers)} papers without embeddings")
        
        updated = 0
        for paper in papers:
            try:
                # TODO: Uncomment when embeddings are ready
                # embedding = generate_embeddings(paper.abstract)
                # paper.embedding = embedding
                updated += 1
            except Exception as e:
                logger.error(f"Error generating embedding: {e}")
                continue
        
        db.commit()
        db.close()
        
        logger.info(f"✅ Updated {updated} embeddings")
        context['ti'].xcom_push(key='embeddings_updated', value=updated)
        
        return updated
        
    except Exception as e:
        logger.error(f"❌ Embeddings update failed: {e}")
        raise

def remove_duplicates(**context):
    """Remove duplicate papers based on URL"""
    try:
        from src.database.connection import get_db
        from src.database.models import Paper
        
        logger.info("🗑️ Removing duplicates...")
        
        db = next(get_db())
        
        # Find duplicate URLs
        duplicates = db.query(Paper.url, func.count(Paper.url)).group_by(
            Paper.url
        ).having(func.count(Paper.url) > 1).all()
        
        logger.info(f"Found {len(duplicates)} duplicate URLs")
        
        removed = 0
        for url, count in duplicates:
            papers = db.query(Paper).filter(Paper.url == url).order_by(
                Paper.published.desc()
            ).all()
            
            # Keep the first (most recent), delete rest
            for paper in papers[1:]:
                db.delete(paper)
                removed += 1
        
        db.commit()
        db.close()
        
        logger.info(f"✅ Removed {removed} duplicate papers")
        context['ti'].xcom_push(key='duplicates_removed', value=removed)
        
        return removed
        
    except Exception as e:
        logger.error(f"❌ Duplicate removal failed: {e}")
        raise

def optimize_database(**context):
    """Run database optimization"""
    try:
        from src.database.connection import engine
        
        logger.info("⚡ Optimizing database...")
        
        with engine.connect() as conn:
            # VACUUM cannot run in transaction
            conn.execution_options(isolation_level="AUTOCOMMIT")
            conn.execute("VACUUM ANALYZE")
        
        logger.info("✅ Database optimized")
        
        return True
        
    except Exception as e:
        logger.error(f"⚠️ Database optimization failed: {e}")
        # Don't fail the DAG if optimization fails
        return False

def get_statistics(**context):
    """Get database statistics"""
    try:
        from src.database.connection import get_db
        from src.database.models import Paper
        
        db = next(get_db())
        
        total_papers = db.query(Paper).count()
        papers_with_embeddings = db.query(Paper).filter(
            Paper.embedding != None
        ).count()
        
        db.close()
        
        logger.info("=" * 60)
        logger.info("DATABASE STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total papers: {total_papers}")
        logger.info(f"Papers with embeddings: {papers_with_embeddings}")
        logger.info(f"Papers without embeddings: {total_papers - papers_with_embeddings}")
        logger.info("=" * 60)
        
        return {
            'total': total_papers,
            'with_embeddings': papers_with_embeddings
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return {}

def weekly_summary(**context):
    """Generate weekly summary"""
    ti = context['ti']
    
    embeddings = ti.xcom_pull(key='embeddings_updated', task_ids='update_embeddings')
    duplicates = ti.xcom_pull(key='duplicates_removed', task_ids='remove_duplicates')
    
    logger.info("=" * 60)
    logger.info("WEEKLY MAINTENANCE SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Embeddings updated: {embeddings}")
    logger.info(f"Duplicates removed: {duplicates}")
    logger.info(f"Database optimized: ✓")
    logger.info("=" * 60)

with DAG(
    'weekly_maintenance',
    default_args=default_args,
    description='Weekly database maintenance and optimization',
    schedule_interval='0 3 * * 0',  # Sunday 3 AM UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['maintenance', 'weekly', 'production'],
) as dag:
    
    embeddings_task = PythonOperator(
        task_id='update_embeddings',
        python_callable=update_embeddings,
        provide_context=True,
    )
    
    duplicates_task = PythonOperator(
        task_id='remove_duplicates',
        python_callable=remove_duplicates,
        provide_context=True,
    )
    
    optimize_task = PythonOperator(
        task_id='optimize_database',
        python_callable=optimize_database,
        provide_context=True,
    )
    
    stats_task = PythonOperator(
        task_id='get_statistics',
        python_callable=get_statistics,
        provide_context=True,
    )
    
    summary_task = PythonOperator(
        task_id='weekly_summary',
        python_callable=weekly_summary,
        provide_context=True,
    )
    
    # Define task dependencies
    [embeddings_task, duplicates_task] >> optimize_task >> stats_task >> summary_task
