import psycopg # type: ignore
from psycopg.pool import ConnectionPool # type: ignore
import chromadb # type: ignore
from chromadb.utils import embedding_functions # type: ignore
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Global instances
pg_pool = None
chroma_client = None
chroma_collection = None
embedding_func = None

def init_db():
    global pg_pool, chroma_client, chroma_collection, embedding_func

    # Initialize Postgres Connection Pool
    conninfo = f"dbname={settings.POSTGRES_DB} user={settings.POSTGRES_USER} password={settings.POSTGRES_PASSWORD} host={settings.POSTGRES_HOST} port={settings.POSTGRES_PORT}"
    try:
        pg_pool = ConnectionPool(conninfo=conninfo, min_size=1, max_size=10)
        logger.info("PostgreSQL connection pool initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL connection pool: {e}")
        raise e

    # Initialize ChromaDB
    try:
        chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
        embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=settings.EMBEDDING_MODEL_NAME)
        # Get or create collection
        try:
            chroma_collection = chroma_client.get_collection(name="documents", embedding_function=embedding_func)
        except Exception:
            chroma_collection = chroma_client.create_collection(name="documents", embedding_function=embedding_func)
        logger.info("ChromaDB initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")
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

def get_chroma_collection():
    if not chroma_collection:
        raise Exception("ChromaDB not initialized. Call init_db() first.")
    return chroma_collection
