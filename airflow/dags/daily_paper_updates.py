"""
Airflow DAG: Daily Research Paper Updates
Fixed imports for Airflow environment
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging

# Setup logging
logger = logging.getLogger(__name__)

def fetch_and_store_papers(topic: str, max_results: int = 20):
    """
    Fetch papers from ArXiv and store in NeonDB
    """
    import sys
    import os
    
    # Add paths
    sys.path.insert(0, '/app')
    sys.path.insert(0, '/app/src')
    
    logger.info(f"🔍 Starting fetch for: {topic}")
    
    try:
        # Import inside function to avoid startup errors
        import requests
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # Database URL
        DATABASE_URL = os.getenv(
            'DATABASE_URL',
            'postgresql://neondb_owner:npg_4DeVUzdo2RYs@ep-frosty-queen-ahy6nn7k-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
        )
        
        # Fetch from ArXiv
        logger.info(f"Fetching papers for: {topic}")
        
        import arxiv
        
        search = arxiv.Search(
            query=topic,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        papers = []
        for result in search.results():
            paper_data = {
                'arxiv_id': result.entry_id.split('/')[-1],
                'title': result.title,
                'authors': ', '.join([author.name for author in result.authors]),
                'abstract': result.summary,
                'url': result.pdf_url,
                'published': result.published.isoformat(),
                'category': result.primary_category
            }
            papers.append(paper_data)
        
        if not papers:
            logger.warning(f"No papers found for: {topic}")
            return
        
        logger.info(f"✅ Found {len(papers)} papers")
        
        # Connect to database
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        saved = 0
        
        for paper_data in papers:
            try:
                # Check if exists
                result = session.execute(
                    "SELECT id FROM papers WHERE arxiv_id = :arxiv_id",
                    {"arxiv_id": paper_data['arxiv_id']}
                ).fetchone()
                
                if result:
                    continue
                
                # Insert new paper
                session.execute(
                    """
                    INSERT INTO papers (
                        arxiv_id, title, authors, abstract, pdf_url, 
                        published_date, primary_category, categories, indexed
                    ) VALUES (
                        :arxiv_id, :title, :authors, :abstract, :url,
                        :published, :category, :category, true
                    )
                    """,
                    paper_data
                )
                
                saved += 1
                
            except Exception as e:
                logger.error(f"Error saving paper: {e}")
                continue
        
        session.commit()
        session.close()
        
        logger.info(f"✅ Saved {saved} new papers for {topic}")
        
    except Exception as e:
        logger.error(f"❌ Error in fetch_and_store: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

def fetch_ai_papers():
    """Fetch AI/ML papers"""
    fetch_and_store_papers("artificial intelligence machine learning deep learning", 20)

def fetch_nlp_papers():
    """Fetch NLP papers"""
    fetch_and_store_papers("natural language processing transformers BERT GPT", 20)

def fetch_cv_papers():
    """Fetch Computer Vision papers"""
    fetch_and_store_papers("computer vision CNN image recognition", 20)

def fetch_rl_papers():
    """Fetch Reinforcement Learning papers"""
    fetch_and_store_papers("reinforcement learning Q-learning policy gradient", 15)

def cleanup_cache():
    """Clear Redis cache"""
    import redis
    import os
    
    logger.info("🗑️ Clearing Redis cache...")
    
    try:
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        
        client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=0,
            decode_responses=True
        )
        
        keys = client.keys("search:*")
        if keys:
            cleared = client.delete(*keys)
            logger.info(f"✅ Cleared {cleared} cache entries")
        else:
            logger.info("No cache entries to clear")
            
    except Exception as e:
        logger.warning(f"⚠️ Cache clear error: {e}")

# DAG configuration
default_args = {
    'owner': 'research-curator',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create DAG
dag = DAG(
    'daily_paper_updates',
    default_args=default_args,
    description='Fetch latest research papers daily from ArXiv',
    schedule_interval='0 2 * * *',  # 2 AM daily
    catchup=False,
    tags=['research', 'papers', 'arxiv', 'automation'],
)

# Define tasks
task_ai = PythonOperator(
    task_id='fetch_ai_papers',
    python_callable=fetch_ai_papers,
    dag=dag,
)

task_nlp = PythonOperator(
    task_id='fetch_nlp_papers',
    python_callable=fetch_nlp_papers,
    dag=dag,
)

task_cv = PythonOperator(
    task_id='fetch_cv_papers',
    python_callable=fetch_cv_papers,
    dag=dag,
)

task_rl = PythonOperator(
    task_id='fetch_rl_papers',
    python_callable=fetch_rl_papers,
    dag=dag,
)

task_cleanup = PythonOperator(
    task_id='cleanup_cache',
    python_callable=cleanup_cache,
    dag=dag,
)

# Set dependencies - run fetches in parallel, then cleanup
[task_ai, task_nlp, task_cv, task_rl] >> task_cleanup
