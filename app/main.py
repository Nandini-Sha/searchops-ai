from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import psycopg
from pydantic import BaseModel
from typing import List, Optional, Any
import uvicorn
from contextlib import asynccontextmanager
import logging

from app.database import init_db, close_db, get_pg_connection, get_chroma_collection
from app.services.search import HybridSearchEngine
from app.services.ingest import run_ingestion
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Response Models
class SearchResult(BaseModel):
    doc_id: str
    score: float
    title: str
    author_name: str
    content_snippet: str
    source: str
    source_type: str
    rrf_score: Optional[float] = None

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    error: Optional[str] = None

engine: Optional[HybridSearchEngine] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    try:
        init_db()
        engine = HybridSearchEngine()
        
        # Check if database is empty
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("SELECT COUNT(*) FROM documents")
                    row = cur.fetchone()
                    pg_count = row[0] if row else 0
                except psycopg.Error:
                    conn.rollback()
                    pg_count = 0
                    
        try:
            col = get_chroma_collection()
            chroma_count = col.count()
        except ValueError:
            chroma_count = 0
            
        if pg_count == 0 or chroma_count == 0:
            logger.info(f"DB Check - Postgres: {pg_count}, Chroma: {chroma_count}. Running auto-ingestion...")
            run_ingestion()
        else:
            logger.info(f"Found {pg_count} Postgres docs and {chroma_count} Chroma docs. Skipping auto-ingestion.")
            
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        
    yield
    
    close_db()

app = FastAPI(
    title="SearchOps AI API",
    description="Agentic Enterprise Search Engine API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/search", response_model=SearchResponse)
def search(q: str = Query(..., description="The search query")):
    """
    Perform a hybrid search using both Vector similarity and SQL Phonetic exact matches.
    """
    if engine is None:
        raise HTTPException(status_code=500, detail="Search engine not initialized")
        
    try:
        results = engine.hybrid_search(q)
        return SearchResponse(query=q, results=results)
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

dist_path = "dist" if os.path.exists("dist") else "frontend/dist"
if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
