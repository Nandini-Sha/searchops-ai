import psycopg # type: ignore
from app.database import get_pg_connection
from typing import List, Dict, Any
from app.services.ingest import get_huggingface_embedding
import logging

logger = logging.getLogger(__name__)

class HybridSearchEngine:
    def vector_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Semantic search using Vector Embeddings via pgvector"""
        try:
            query_embedding = get_huggingface_embedding(query)
        except Exception as e:
            logger.error(f"Failed to get query embedding: {e}")
            return []
            
        search_results = []
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                try:
                    # Use cosine distance <=>
                    cur.execute("""
                        SELECT doc_id, title, author_name, content, source_type, 1 - (embedding <=> %s::vector) AS score
                        FROM documents
                        WHERE embedding IS NOT NULL
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s
                    """, (query_embedding, query_embedding, k))
                    
                    rows = cur.fetchall()
                    for row in rows:
                        doc_id, title, author, content, source_type, score = row
                        search_results.append({
                            "doc_id": str(doc_id),
                            "score": float(score),
                            "title": title,
                            "author_name": author,
                            "content_snippet": content[:150] + "...",
                            "source": "vector",
                            "source_type": source_type
                        })
                except psycopg.Error as e:
                    logger.error(f"SQL Vector Search failed: {e}")
                    conn.rollback()
                    
        return search_results

    def phonetic_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Keyword and Phonetic Search via PostgreSQL"""
        # Split query into words to check against soundex
        words = query.split()
        search_results = []
        
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                for word in words:
                    if len(word) < 3:
                        continue # Skip small words for soundex
                    
                    # Find documents where author name matches phonetically, or content contains keyword
                    like_term = f"%{word}%"
                    try:
                        cur.execute("""
                            SELECT doc_id, title, author_name, content, source_type 
                            FROM documents
                            WHERE 
                                EXISTS (
                                    SELECT 1 FROM unnest(string_to_array(author_name, ' ')) AS name_part 
                                    WHERE soundex(name_part) = soundex(%s)
                                ) OR
                                author_name ILIKE %s OR 
                                title ILIKE %s OR
                                content ILIKE %s
                            LIMIT %s
                        """, (word, like_term, like_term, like_term, k))
                        
                        rows = cur.fetchall()
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
                    except psycopg.Error as e:
                        print(f"SQL Phonetic Search failed (fallback to vector only): {e}")
                        conn.rollback()
        
        return search_results[:k]

    def hybrid_search(self, query: str, k: int = 20) -> List[Dict[str, Any]]:
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
