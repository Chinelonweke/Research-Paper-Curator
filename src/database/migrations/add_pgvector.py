"""
Database Migration: Add pgvector extension and paper_chunks table
Run this script to set up the RAG infrastructure in your NeonDB database.

Usage:
    python -m src.database.migrations.add_pgvector
"""
import os
import sys
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


def run_migration():
    """Run the pgvector migration"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False

    print(f"Connecting to database...")
    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            # Enable pgvector extension
            print("1. Enabling pgvector extension...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            print("   pgvector extension enabled")

            # Create paper_chunks table
            print("2. Creating paper_chunks table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS paper_chunks (
                    id SERIAL PRIMARY KEY,
                    paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    embedding vector(384),
                    start_char INTEGER,
                    end_char INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.commit()
            print("   paper_chunks table created")

            # Create indexes
            print("3. Creating indexes...")

            # Index for paper lookups
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS paper_chunks_paper_id_idx
                ON paper_chunks(paper_id);
            """))
            conn.commit()
            print("   Paper ID index created")

            # Vector similarity index (IVFFlat)
            # Note: This requires at least some data to build the index
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS paper_chunks_embedding_idx
                    ON paper_chunks USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
                """))
                conn.commit()
                print("   Vector similarity index created")
            except Exception as e:
                print(f"   Warning: Could not create vector index (may need data first): {e}")
                # Create HNSW index as alternative (works without data)
                try:
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS paper_chunks_embedding_hnsw_idx
                        ON paper_chunks USING hnsw (embedding vector_cosine_ops);
                    """))
                    conn.commit()
                    print("   HNSW vector index created instead")
                except Exception as e2:
                    print(f"   Warning: Could not create HNSW index: {e2}")

            print("\nMigration completed successfully!")
            print("\nNext steps:")
            print("  1. Rebuild the API: docker-compose --env-file .env -f docker/docker-compose.yml up api --build")
            print("  2. Index papers: POST /api/papers/index-all")
            print("  3. Test RAG: POST /api/ask with a question")

            return True

        except Exception as e:
            print(f"ERROR: Migration failed: {e}")
            conn.rollback()
            return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
