from app.services.search import HybridSearchEngine
from app.database import init_db, close_db

def run_tests():
    init_db()
    engine = HybridSearchEngine()
    
    print("===========================================")
    print("Test 1: Semantic Query ('server went down')")
    print("===========================================")
    # We expect this to match the Slack messages about the redis outage
    # mainly through vector search.
    results = engine.hybrid_search("server went down")
    for i, res in enumerate(results):
        print(f"Rank {i+1}: {res['title']} (Score: {res['rrf_score']}, Source: {res['source']})")
    
    print("\\n===========================================")
    print("Test 2: Phonetic Query ('Smithe')")
    print("===========================================")
    # We expect this to match Bob Smith and Alice Smythe via Soundex
    results = engine.hybrid_search("Smithe")
    for i, res in enumerate(results):
        print(f"Rank {i+1}: {res['title']} - {res['author_name']} (Score: {res['rrf_score']}, Source: {res['source']})")

    print("\\n===========================================")
    print("Test 3: Exact Code Search ('legacy_handlers')")
    print("===========================================")
    # We expect this to match the code snippet or the slack msg mentioning it
    results = engine.hybrid_search("legacy_handlers")
    for i, res in enumerate(results):
        print(f"Rank {i+1}: {res['title']} (Score: {res['rrf_score']}, Source: {res['source']})")
        
    close_db()

if __name__ == "__main__":
    run_tests()
