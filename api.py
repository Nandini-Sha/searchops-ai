from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import psycopg2
from search_engine import HybridSearchEngine
from ingest import run_ingestion
import uvicorn

app = FastAPI(
    title="SearchOps AI API",
    description="Agentic Enterprise Search Engine API",
    version="1.0.0"
)

# Enable CORS for the future React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the search engine once
engine = HybridSearchEngine()

@app.on_event("startup")
def startup_event():
    # Check if database is empty (ephemeral disk on Render free tier)
    pg_host = os.environ.get("POSTGRES_HOST", "localhost")
    pg_port = os.environ.get("POSTGRES_PORT", "5432") # Default internal docker port
    
    try:
        conn = psycopg2.connect(
            dbname="searchops",
            user="admin",
            password="adminpassword",
            host=pg_host,
            port=pg_port
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM documents")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        if count == 0:
            print("Database empty! Running auto-ingestion for ephemeral deployment...")
            run_ingestion()
        else:
            print(f"Found {count} documents. Skipping auto-ingestion.")
    except Exception as e:
        print(f"Startup DB check failed (this is normal if DB is still booting): {e}")

@app.get("/search")
def search(q: str = Query(..., description="The search query")):
    """
    Perform a hybrid search using both Vector similarity and SQL Phonetic exact matches.
    """
    results = engine.hybrid_search(q)
    return {"query": q, "results": results}

# Serve React frontend in production
dist_path = "dist" if os.path.exists("dist") else "frontend/dist"
if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000)
