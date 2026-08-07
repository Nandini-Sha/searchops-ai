import os
import psycopg2 # type: ignore
import chromadb # type: ignore
from chromadb.utils import embedding_functions # type: ignore

class HybridSearchEngine:
    def __init__(self):
        # Connect to PostgreSQL
        pg_host = os.environ.get("POSTGRES_HOST", "localhost")
        pg_port = os.environ.get("POSTGRES_PORT", "5432")
        pg_user = os.environ.get("POSTGRES_USER", "admin")
        pg_password = os.environ.get("POSTGRES_PASSWORD", "adminpassword")
        pg_dbname = os.environ.get("POSTGRES_DB", "searchops")
        
        self.conn = psycopg2.connect(
            dbname=pg_dbname,
            user=pg_user,
            password=pg_password,
            host=pg_host,
            port=pg_port
        )
        self.cur = self.conn.cursor()
        
        # Connect to ChromaDB
        self.chroma_client = chromadb.PersistentClient(path="./data/chroma")
        self.embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.chroma_client.get_collection(name="documents", embedding_function=self.embedding_func)
        
    def vector_search(self, query: str, k: int = 5):
        """Semantic search using Vector Embeddings via ChromaDB"""
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )
        
        # Parse ChromaDB output
        search_results = []
        if results['ids']:
            ids = results['ids'][0]
            distances = results['distances'][0]
            metadatas = results['metadatas'][0]
            documents = results['documents'][0]
            
            for i in range(len(ids)):
                search_results.append({
                    "doc_id": ids[i],
                    "score": 1.0 / (1.0 + distances[i]), # Convert distance to a pseudo-score (higher is better)
                    "title": metadatas[i].get("title", ""),
                    "author_name": metadatas[i].get("author_name", ""),
                    "content_snippet": documents[i][:150] + "...",
                    "source": "vector",
                    "source_type": metadatas[i].get("source_type", "")
                })
        return search_results

    def phonetic_search(self, query: str, k: int = 5):
        """Keyword and Phonetic Search via PostgreSQL"""
        # Split query into words to check against soundex
        words = query.split()
        search_results = []
        
        for word in words:
            if len(word) < 3:
                continue # Skip small words for soundex
            
            # Find documents where author name matches phonetically, or content/title contains keyword
            like_term = f"%{word}%"
            try:
                self.cur.execute("""
                    SELECT doc_id, title, author_name, content, source_type 
                    FROM documents
                    WHERE 
                        author_name ILIKE %s OR 
                        title ILIKE %s OR
                        content ILIKE %s
                    LIMIT %s
                """, (like_term, like_term, like_term, k))
                
                rows = self.cur.fetchall()
                for row in rows:
                    doc_id, title, author, content, source_type = row
                    
                    # Check if we already added this doc
                    if not any(r['doc_id'] == doc_id for r in search_results):
                        search_results.append({
                            "doc_id": doc_id,
                            "score": 1.0, # Flat score for SQL matches
                            "title": title,
                            "author_name": author,
                            "content_snippet": content[:150] + "...",
                            "source": "sql_phonetic",
                            "source_type": source_type
                        })
            except psycopg2.Error as e:
                print(f"SQL Phonetic Search failed (fallback to vector only): {e}")
                self.conn.rollback()
        
        return search_results[:k]

    def hybrid_search(self, query: str, k: int = 20):
        """Combines Vector and Phonetic Search using Reciprocal Rank Fusion (RRF)"""
        vector_results = self.vector_search(query, k=k*2) # Fetch more to fuse
        sql_results = self.phonetic_search(query, k=k*2)
        
        # RRF logic: score = 1 / (60 + rank)
        rrf_scores = {}
        document_map = {}
        
        # Process vector results
        for rank, doc in enumerate(vector_results):
            doc_id = doc["doc_id"]
            document_map[doc_id] = doc
            rrf_scores[doc_id] = 1.0 / (60 + rank + 1)
            
        # Process SQL results
        for rank, doc in enumerate(sql_results):
            doc_id = doc["doc_id"]
            if doc_id not in document_map:
                document_map[doc_id] = doc
                doc["source"] = "sql_phonetic" # If it's new
            else:
                document_map[doc_id]["source"] = "hybrid" # It was found by both!
                
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = 0.0
            rrf_scores[doc_id] += 1.0 / (60 + rank + 1)
            
        # Sort by RRF score descending
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Build final top K
        final_results = []
        for doc_id, score in sorted_docs[:k]:
            doc_info = document_map[doc_id]
            doc_info["rrf_score"] = round(score, 4)
            final_results.append(doc_info)
            
        return final_results
        
    def close(self):
        self.cur.close()
        self.conn.close()

if __name__ == "__main__":
    import sys
    engine = HybridSearchEngine()
    
    query = sys.argv[1] if len(sys.argv) > 1 else "server crash"
    print(f"\\n=== Hybrid Search Results for: '{query}' ===")
    
    results = engine.hybrid_search(query)
    for i, res in enumerate(results):
        print(f"\\nRank {i+1} (Score: {res['rrf_score']}, Found via: {res['source']})")
        print(f"Title: {res['title']}")
        print(f"Author: {res['author_name']}")
        print(f"Snippet: {res['content_snippet']}")
        
    engine.close()
