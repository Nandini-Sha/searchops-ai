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
    if settings.DATABASE_URL:
        conninfo = settings.DATABASE_URL
    else:
        conninfo = f"dbname={settings.POSTGRES_DB} user={settings.POSTGRES_USER} password={settings.POSTGRES_PASSWORD} host={settings.POSTGRES_HOST} port={settings.POSTGRES_PORT}"
    
    try:
        def configure(conn):
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
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
