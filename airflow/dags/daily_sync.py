"""
Daily sync DAG - Fetches and processes new papers from arXiv.
Runs every day at 2 AM.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from airflow.utils.dates import days_ago
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.ingestion.processor import get_paper_processor
from src.core.logging_config import app_logger


# Default arguments
default_args = {
    'owner': 'rag-system',
    'depends_on_past': False,
    'email': ['admin@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
}


def fetch_recent_papers(**context):
    """Fetch papers from the last day."""
    try:
        app_logger.info("Starting daily paper fetch")
        
        processor = get_paper_processor()
        stats = processor.process_recent_papers(
            days_back=1,  # Last 24 hours
            max_results=100
        )
        
        app_logger.info(f"Daily sync completed: {stats}")
        
        # Push stats to XCom for downstream tasks
        context['task_instance'].xcom_push(key='fetch_stats', value=stats)
        
        return stats
        
    except Exception as e:
        app_logger.error(f"Error in daily fetch: {e}", exc_info=True)
        raise


def validate_processing(**context):
    """Validate that processing completed successfully."""
    try:
        # Get stats from previous task
        stats = context['task_instance'].xcom_pull(
            task_ids='fetch_papers',
            key='fetch_stats'
        )
        
        if not stats:
            raise ValueError("No stats received from fetch task")
        
        # Check for failures
        if stats.get('failed', 0) > 0:
            app_logger.warning(f"Some papers failed to process: {stats['failed']}")
        
        # Check if any papers were processed
        total_processed = stats.get('new', 0) + stats.get('updated', 0)
        if total_processed == 0:
            app_logger.info("No new papers to process today")
        else:
            app_logger.info(f"Successfully processed {total_processed} papers")
        
        context['task_instance'].xcom_push(key='validation_result', value=True)
        
        return True
        
    except Exception as e:
        app_logger.error(f"Validation failed: {e}", exc_info=True)
        raise


def send_summary_report(**context):
    """Generate and send summary report."""
    try:
        stats = context['task_instance'].xcom_pull(
            task_ids='fetch_papers',
            key='fetch_stats'
        )
        
        report = f"""
        Daily Sync Report - {datetime.now().strftime('%Y-%m-%d')}
        
        Summary:
        - Fetched: {stats.get('fetched', 0)} papers
        - New: {stats.get('new', 0)} papers
        - Updated: {stats.get('updated', 0)} papers
        - Skipped: {stats.get('skipped', 0)} papers
        - Failed: {stats.get('failed', 0)} papers
        
        Status: {'Success' if stats.get('failed', 0) == 0 else 'Completed with errors'}
        """
        
        app_logger.info(report)
        
        return report
        
    except Exception as e:
        app_logger.error(f"Error generating report: {e}", exc_info=True)
        raise


# Define the DAG
dag = DAG(
    'daily_paper_sync',
    default_args=default_args,
    description='Daily synchronization of arXiv papers',
    schedule_interval='0 2 * * *',  # 2 AM every day
    start_date=days_ago(1),
    catchup=False,
    tags=['ingestion', 'daily', 'arxiv'],
)


# Define tasks
fetch_papers_task = PythonOperator(
    task_id='fetch_papers',
    python_callable=fetch_recent_papers,
    provide_context=True,
    dag=dag,
)

validate_task = PythonOperator(
    task_id='validate_processing',
    python_callable=validate_processing,
    provide_context=True,
    dag=dag,
)

report_task = PythonOperator(
    task_id='generate_report',
    python_callable=send_summary_report,
    provide_context=True,
    dag=dag,
)

# Optional: Send email with report
# email_task = EmailOperator(
#     task_id='send_email_report',
#     to='admin@example.com',
#     subject='Daily RAG Sync Report - {{ ds }}',
#     html_content='{{ task_instance.xcom_pull(task_ids="generate_report") }}',
#     dag=dag,
# )


# Define task dependencies
fetch_papers_task >> validate_task >> report_task
# If using email: report_task >> email_task