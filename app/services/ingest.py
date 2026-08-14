import json
import os
import uuid
import requests
import psycopg # type: ignore
from app.config import settings
from app.database import get_pg_connection
import logging

logger = logging.getLogger(__name__)

def get_huggingface_embedding(text: str) -> list[float]:
    hf_token = settings.HF_TOKEN
    model = settings.EMBEDDING_MODEL_NAME
    if not hf_token:
        raise ValueError("HF_TOKEN is required for vector generation.")
    
    api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model}"
    headers = {"Authorization": f"Bearer {hf_token}"}
    
    response = requests.post(api_url, headers=headers, json={"inputs": [text]})
    if response.status_code != 200:
        raise Exception(f"Failed to get embedding: {response.text}")
    
    result = response.json()
    if isinstance(result, list) and isinstance(result[0], list):
        return result[0]
    return result

def insert_document(source_type, source_url, title, content, author_name):
    doc_id = str(uuid.uuid4())
    
    text_to_embed = f"Title: {title}\nAuthor: {author_name}\nContent: {content}"
    try:
        embedding = get_huggingface_embedding(text_to_embed)
    except Exception as e:
        logger.error(f"Error getting embedding for {title}: {e}")
        return

    # Insert into PostgreSQL
    with get_pg_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO documents (doc_id, source_type, source_url, title, content, author_name, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (doc_id, source_type, source_url, title, content, author_name, embedding))
            conn.commit()

def ingest_slack():
    logger.info("Ingesting Slack messages...")
    with open(os.path.join(settings.MOCK_DATA_DIR, "slack_messages.json"), "r", encoding="utf-8") as f:
        messages = json.load(f)
    
    for msg in messages:
        insert_document(
            source_type="slack",
            source_url=f"slack://{msg['channel']}/{msg['id']}",
            title=f"Slack Message in #{msg['channel']}",
            content=msg['text'],
            author_name=msg['author']
        )

def ingest_confluence():
    logger.info("Ingesting Confluence docs...")
    base_dir = os.path.join(settings.MOCK_DATA_DIR, "confluence_docs")
    if not os.path.exists(base_dir):
        logger.warning(f"Confluence docs directory not found: {base_dir}")
        return
        
    for filename in os.listdir(base_dir):
        if filename.endswith(".md"):
            with open(os.path.join(base_dir, filename), "r", encoding="utf-8") as f:
                content = f.read()
            
            # Simple parsing: first line is title, second is author
            lines = content.split('\n')
            title = lines[0].replace("# ", "").strip()
            author = lines[1].replace("Author: ", "").strip() if len(lines) > 1 and "Author:" in lines[1] else "Unknown"
            
            insert_document(
                source_type="confluence",
                source_url=f"confluence://{filename}",
                title=title,
                content=content,
                author_name=author
            )

def ingest_github():
    logger.info("Ingesting GitHub repos...")
    base_dir = os.path.join(settings.MOCK_DATA_DIR, "github_repos")
    if not os.path.exists(base_dir):
        logger.warning(f"GitHub repos directory not found: {base_dir}")
        return
        
    for repo in os.listdir(base_dir):
        repo_dir = os.path.join(base_dir, repo)
        if os.path.isdir(repo_dir):
            for filename in os.listdir(repo_dir):
                filepath = os.path.join(repo_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                insert_document(
                    source_type="github",
                    source_url=f"github://{repo}/{filename}",
                    title=f"{repo}/{filename}",
                    content=content,
                    author_name="Unknown" # We didn't add author to github files strictly, except in README
                )

def run_ingestion():
    logger.info("Starting auto-ingestion process...")
    # Initialize database schema if it doesn't exist
    with get_pg_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    doc_id UUID DEFAULT gen_random_uuid(),
                    source_type VARCHAR(50) NOT NULL,
                    source_url VARCHAR(255),
                    title VARCHAR(255),
                    content TEXT NOT NULL,
                    author_name VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB,
                    embedding vector(384)
                );
            """)
            
            # Clear existing data in PG
            cur.execute("TRUNCATE TABLE documents RESTART IDENTITY;")
            conn.commit()
            
    try:
        import generate_mock_data
        generate_mock_data.generate_slack_messages()
        generate_mock_data.generate_confluence_docs()
        generate_mock_data.generate_github_repos()
    except Exception as e:
        logger.error(f"Failed to generate mock data: {e}")
    
    ingest_slack()
    ingest_confluence()
    ingest_github()
    
    logger.info("Ingestion complete!")

if __name__ == "__main__":
    import app.database
    app.database.init_db()
    run_ingestion()
