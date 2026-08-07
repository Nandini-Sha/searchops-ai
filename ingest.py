import json
import os
import uuid
import psycopg2 # type: ignore
import chromadb # type: ignore
from chromadb.utils import embedding_functions # type: ignore

# Connect to PostgreSQL
pg_host = os.environ.get("POSTGRES_HOST", "localhost")
pg_port = os.environ.get("POSTGRES_PORT", "5433")
pg_user = os.environ.get("POSTGRES_USER", "admin")
pg_password = os.environ.get("POSTGRES_PASSWORD", "adminpassword")
pg_dbname = os.environ.get("POSTGRES_DB", "searchops")

conn = psycopg2.connect(
    dbname=pg_dbname,
    user=pg_user,
    password=pg_password,
    host=pg_host,
    port=pg_port
)
cur = conn.cursor()

# Connect to ChromaDB
chroma_client = chromadb.PersistentClient(path="./data/chroma")
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Recreate collection to avoid duplicates on multiple runs
try:
    chroma_client.delete_collection(name="documents")
except Exception:
    pass
collection = chroma_client.create_collection(name="documents", embedding_function=embedding_func)

def insert_document(source_type, source_url, title, content, author_name):
    doc_id = str(uuid.uuid4())
    
    # 1. Insert into PostgreSQL
    cur.execute("""
        INSERT INTO documents (doc_id, source_type, source_url, title, content, author_name)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (doc_id, source_type, source_url, title, content, author_name))
    
    # 2. Insert into ChromaDB
    # We store the title and author in the vector DB metadata, but we embed the content (and optionally title).
    text_to_embed = f"Title: {title}\nAuthor: {author_name}\nContent: {content}"
    
    collection.add(
        documents=[text_to_embed],
        metadatas=[{"source_type": source_type, "source_url": source_url, "author_name": author_name, "title": title}],
        ids=[doc_id]
    )

def ingest_slack():
    print("Ingesting Slack messages...")
    with open("data/mock/slack_messages.json", "r", encoding="utf-8") as f:
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
    print("Ingesting Confluence docs...")
    base_dir = "data/mock/confluence_docs"
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
    print("Ingesting GitHub repos...")
    base_dir = "data/mock/github_repos"
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
    print("Starting auto-ingestion process...")
    # Initialize database schema if it doesn't exist
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
            metadata JSONB
        );
    """)
        
    # Clear existing data in PG
    cur.execute("TRUNCATE TABLE documents RESTART IDENTITY;")
    
    ingest_slack()
    ingest_confluence()
    ingest_github()
    
    conn.commit()
    print("Ingestion complete!")

if __name__ == "__main__":
    run_ingestion()
    cur.close()
    conn.close()
