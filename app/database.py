import psycopg # type: ignore
from psycopg_pool import ConnectionPool # type: ignore
from pgvector.psycopg import register_vector # type: ignore
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Global instances
pg_pool = None

def init_db():
    global pg_pool

    # Initialize Postgres Connection Pool
    # Only use DATABASE_URL if it's explicitly a postgres URI to avoid conflicting with other DBs in environment
    db_url = settings.DATABASE_URL.strip() if settings.DATABASE_URL else None
    
    if db_url and db_url.startswith(("postgres://", "postgresql://")):
        conninfo = db_url
        logger.info("Using DATABASE_URL from environment.")
    else:
        if settings.DATABASE_URL:
            logger.warning(f"DATABASE_URL was set but ignored because it doesn't start with postgres:// or postgresql:// (Value starts with: {settings.DATABASE_URL[:10]}...)")
        
        import urllib.parse
        user = urllib.parse.quote(settings.POSTGRES_USER, safe="")
        password = urllib.parse.quote(settings.POSTGRES_PASSWORD, safe="")
        host = urllib.parse.quote(settings.POSTGRES_HOST, safe="")
        dbname = urllib.parse.quote(settings.POSTGRES_DB, safe="")
        conninfo = f"postgresql://{user}:{password}@{host}:{settings.POSTGRES_PORT}/{dbname}"
    
    try:
        def configure(conn):
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.execute("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;")
            conn.commit()
            register_vector(conn)

        pg_pool = ConnectionPool(conninfo=conninfo, min_size=1, max_size=10, configure=configure)
        logger.info("PostgreSQL connection pool initialized with pgvector.")
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL connection pool: {e}")
        raise e

def close_db():
    global pg_pool
    if pg_pool:
        pg_pool.close()
        logger.info("PostgreSQL connection pool closed.")

def get_pg_connection():
    if not pg_pool:
        raise Exception("Database pool not initialized. Call init_db() first.")
    return pg_pool.connection()
