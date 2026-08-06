from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from search_engine import HybridSearchEngine
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
