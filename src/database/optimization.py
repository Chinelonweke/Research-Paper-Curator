"""
Database optimization for heavy loads.
"""
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import Pool
import time
from src.core.logging_config import app_logger


def setup_database_optimizations(engine: Engine):
    """Apply database optimizations for production."""
    
    # Connection pool event listeners
    @event.listens_for(Pool, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Optimize PostgreSQL connection."""
        cursor = dbapi_conn.cursor()
        # Set statement timeout (30 seconds)
        cursor.execute("SET statement_timeout = 30000")
        # Use prepared statements
        cursor.execute("SET plan_cache_mode = force_generic_plan")
        cursor.close()
    
    # Query performance monitoring
    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault('query_start_time', []).append(time.time())
    
    @event.listens_for(Engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = time.time() - conn.info['query_start_time'].pop()
        
        # Log slow queries
        if total > 1.0:  # > 1 second
            app_logger.warning(
                f"SLOW QUERY ({total:.2f}s): {statement[:200]}"
            )


def create_indexes(engine: Engine):
    """Create additional indexes for performance."""
    with engine.connect() as conn:
        # Composite indexes for common queries
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_papers_category_date 
            ON papers(primary_category, published_date DESC);
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chunks_paper_type 
            ON chunks(paper_id, chunk_type);
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_search_logs_timestamp 
            ON search_logs(timestamp DESC);
        """))
        
        # Partial indexes for frequent queries
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_papers_indexed 
            ON papers(indexed) 
            WHERE indexed IS NOT NULL;
        """))
        
        conn.commit()
        app_logger.info("Created performance indexes")


def optimize_queries():
    """SQL query optimization examples."""
    
    # Use EXPLAIN ANALYZE to check query plans
    examples = """
    -- Check query plan
    EXPLAIN ANALYZE 
    SELECT * FROM papers 
    WHERE primary_category = 'cs.AI' 
    ORDER BY published_date DESC 
    LIMIT 20;
    
    -- Vacuum and analyze tables
    VACUUM ANALYZE papers;
    VACUUM ANALYZE chunks;
    
    -- Update statistics
    ANALYZE papers;
    
    -- Check index usage
    SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
    FROM pg_stat_user_indexes
    ORDER BY idx_scan DESC;
    
    -- Find missing indexes
    SELECT schemaname, tablename, attname, n_distinct, correlation
    FROM pg_stats
    WHERE schemaname = 'public'
    ORDER BY abs(correlation) DESC;
    """
    
    return examples