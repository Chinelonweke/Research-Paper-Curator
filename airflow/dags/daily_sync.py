"""
Daily ArXiv Sync DAG
Runs every day at 2 AM UTC
Fetches new papers from ArXiv and saves to NeonDB
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging
import uuid

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'research-curator',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
}

def fetch_daily_papers(**context):
    """Fetch papers from ArXiv published in last 24 hours"""
    try:
        from src.ingestion.arxiv_fetcher import ArxivFetcher
        from src.database.connection import get_db
        from src.database.models import Paper
        
        logger.info("🚀 Starting daily ArXiv sync...")
        
        # Initialize fetcher
        fetcher = ArxivFetcher()
        
        # Fetch recent papers from multiple categories
        categories = ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.NE"]
        all_papers = []
        
        for category in categories:
            logger.info(f"Fetching from {category}...")
            papers = fetcher.fetch_by_category(
                category=category,
                max_results=20,
                sort_by="SubmittedDate"
            )
            all_papers.extend(papers)
        
        logger.info(f"📚 Fetched {len(all_papers)} papers from ArXiv")
        
        # Save to database
        db = next(get_db())
        saved_count = 0
        skipped_count = 0
        
        for paper_data in all_papers:
            try:
                # Check if paper already exists
                existing = db.query(Paper).filter(
                    Paper.url == paper_data['pdf_url']
                ).first()
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Create new paper
                paper = Paper(
                    id=str(uuid.uuid4()),
                    title=paper_data['title'],
                    authors=', '.join(paper_data['authors']),
                    abstract=paper_data['abstract'],
                    url=paper_data['pdf_url'],
                    published=paper_data['published_date'].strftime('%Y-%m-%d') if paper_data['published_date'] else None,
                    category=paper_data['primary_category']
                )
                
                db.add(paper)
                saved_count += 1
                
            except Exception as e:
                logger.error(f"Error saving paper: {e}")
                continue
        
        db.commit()
        db.close()
        
        logger.info(f"✅ Daily sync complete!")
        logger.info(f"   Saved: {saved_count} new papers")
        logger.info(f"   Skipped: {skipped_count} existing papers")
        
        # Push stats to XCom
        context['ti'].xcom_push(key='saved_count', value=saved_count)
        context['ti'].xcom_push(key='skipped_count', value=skipped_count)
        
        return {
            'saved': saved_count,
            'skipped': skipped_count,
            'total': len(all_papers)
        }
        
    except Exception as e:
        logger.error(f"❌ Daily sync failed: {e}")
        raise

def send_summary(**context):
    """Send summary of daily sync"""
    ti = context['ti']
    saved = ti.xcom_pull(key='saved_count', task_ids='fetch_daily_papers')
    skipped = ti.xcom_pull(key='skipped_count', task_ids='fetch_daily_papers')
    
    logger.info("=" * 60)
    logger.info("DAILY SYNC SUMMARY")
    logger.info("=" * 60)
    logger.info(f"New papers saved: {saved}")
    logger.info(f"Papers skipped: {skipped}")
    logger.info("=" * 60)

with DAG(
    'daily_arxiv_sync',
    default_args=default_args,
    description='Fetch new ArXiv papers daily',
    schedule_interval='0 2 * * *',  # 2 AM UTC daily
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['arxiv', 'daily', 'production'],
) as dag:
    
    fetch_task = PythonOperator(
        task_id='fetch_daily_papers',
        python_callable=fetch_daily_papers,
        provide_context=True,
    )
    
    summary_task = PythonOperator(
        task_id='send_summary',
        python_callable=send_summary,
        provide_context=True,
    )
    
    fetch_task >> summary_task
