# main.py - CORRECTED VERSION with working search
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import os
import sys
import uuid
from datetime import datetime
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from fastapi_server.chromadb_utils import ChromaDBManager
    print("Imported ChromaDBManager")
except ImportError as e:
    print(f" Import error: {e}")

app = FastAPI(title="Gates of Morning API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],)
db_manager =None

@app.on_event("startup")
async def startup_event():
    global db_manager
    try:
        db_manager = ChromaDBManager(collection_name="content_versions")
        print(" Database manager initialized")
    except Exception as e:
        print(f"Database initialization failed: {e}")

class SearchRequest(BaseModel):
    query: str
    limit: int = 5

class SearchResponse(BaseModel):
    query: str
    results: List[Dict[str,Any]]
    search_info: Dict[str,Any]

@app.post("/search/smart", response_model=SearchResponse)
async def smart_search(request: SearchRequest):
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    print(f"=== Search Request ===")
    print(f"Query:'{request.query}'")
    print(f"Limit:{request.limit}")
    
    try:
        doc_count = db_manager.collection.count()
        print(f"Collection has {doc_count} documents")
        
        if doc_count == 0:
            print("No documents in collection")
            return SearchResponse(
                query=request.query,
                results=[],
                search_info={
                    "strategy":"none",
                    "error":"No documents in collection",
                    "database_count":doc_count})
        search_results = db_manager.search(request.query,request.limit)
        print(f"Search returned {len(search_results)} results")
        for i, result in enumerate(search_results):
            print(f"Result {i+1}: Role={result.get('role')}, Score={result.get('score', 0):.2f}")
            print(f"  Content preview: {result.get('content','')[:100]}...")
        return SearchResponse(
            query=request.query,
            results=search_results,
            search_info={ "strategy": "direct_search",
                "results_count": len(search_results),
                "database_count": doc_count,
                "status": "success" } )
        
    except Exception as e:
        print(f"Search error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Search failed: {str(e)}" )

@app.get("/debug/database")
async def debug_database():
    if not db_manager:
        return {"error": "Database not initialized"}
    try:
        count = db_manager.collection.count()
        if count == 0:
            return {
                "count": 0,
                "message": "No documents in collection"}
        result = db_manager.collection.get()
        documents_info = []
        for i, (doc, doc_id, metadata) in enumerate(zip(
            result["documents"], 
            result["ids"], 
            result["metadatas"])):
            documents_info.append({
                "id": doc_id,
                "role": metadata.get("role", "unknown"),
                "timestamp": metadata.get("timestamp", "unknown"),
                "content_length": len(doc),
                "content_preview": doc[:200] + "..." if len(doc) > 200 else doc})
        
        return {"count": count,
            "documents": documents_info}
        
    except Exception as e:
        print(f"Debug database error: {e}")
        return {"error": str(e)}

@app.post("/debug/test-search")
async def test_search():
    if not db_manager:
        return {"error": "Database not initialized"}
    
    test_queries = ["chapter",
        "morning",
        "Gates",
        "Book",
        "summary" ]
    
    results = {}
    
    for query in test_queries:
        try:
            search_results = db_manager.search(query, limit=2)
            results[query] = {
                "count": len(search_results),
                "results": [
                    {
                        "role": r.get("role"),
                        "score": r.get("score", 0),
                        "preview": r.get("content", "")[:100]
                    }
                    for r in search_results] }
        except Exception as e:
            results[query] = {"error": str(e)}
    
    return results

@app.post("/debug/clear")
async def clear_database():
    if not db_manager:
        return {"error": "Database not initialized"}
    
    try:
        db_manager.clear_collection()
        return {"status": "Database cleared"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug/raw-search/{query}")
async def raw_search(query: str):
    if not db_manager:
        return {"error": "Database not initialized"}
    
    try:
        result = db_manager.collection.query(
            query_texts=[query],
            n_results=5)
        
        return {"query": query,
            "raw_result": {
                "documents": result.get("documents", []),
                "distances": result.get("distances", []),
                "metadatas": result.get("metadatas", []),
                "ids": result.get("ids", [])}}
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def root():
    return {
        "message": "Gates of Morning API", 
        "status": "running",
        "database_initialized": db_manager is not None }

class SmartSearch:
    def __init__(self, db_manager):
        self.db = db_manager
        self.learned_values = {"Exact Phrase Match": 0.2,
    "Semantic Search": 0.0,
    "Expanded Keyword Search": 0.0,
    "Mixed Strategy": 0.0}

    
    def search(self, query, limit=5):
        return self.db.search(query, limit)

class WorkflowRunner:
    def __init__(self,db_manager,searcher):
        self.db =db_manager
        self.searcher = searcher
    
    async def run_full_pipeline(self,url):
        workflow_id =uuid.uuid4().hex[:6]
        
        try:
            from scraping.scrape_chapter import scrape_chapter
            from ai_pipeline.ai_pipeline import rewrite, review

            data_dir = os.path.join(project_root, "data")
            os.makedirs(data_dir,exist_ok=True)
            screenshot_path = os.path.join(data_dir,"screenshot.png")
            scraped_path = os.path.join(data_dir,"scraped.txt")
            rewritten_path = os.path.join(data_dir,"rewritten.txt")
            reviewed_path = os.path.join(data_dir,"reviewed.txt")
            
            print("Step 1: Scraping...")
            await scrape_chapter(url, screenshot_path, scraped_path)
            with open(scraped_path, 'r', encoding='utf-8') as f:
                scraped_content = f.read()
            scraper_id = self.db.store_version(
                scraped_content, 
                "scraper", 
                {"url": url})
            print("Step 2: Rewriting...")
            rewritten_content = rewrite(scraped_content)
            with open(rewritten_path,'w',encoding='utf-8') as f:
                f.write(rewritten_content)
            rewriter_id = self.db.store_version(
                rewritten_content,
                "ai_writer",
                {"source":scraper_id})
            
            print("Step 3: Reviewing...")
            reviewed_content = review(rewritten_content)
            with open(reviewed_path, 'w', encoding='utf-8') as f:
                f.write(reviewed_content)
            reviewer_id = self.db.store_version(
                reviewed_content,
                "ai_reviewer", 
                {"source": rewriter_id})
            
            return {"workflow_id": workflow_id,
                "status": "success",
                "original_size": len(scraped_content),
                "rewritten_size": len(rewritten_content),
                "reviewed_size": len(reviewed_content),
                "files_created": [screenshot_path, scraped_path, rewritten_path, reviewed_path],
                "document_ids": [scraper_id, rewriter_id, reviewer_id],
                "next": "ready for human editing"}
            
        except Exception as e:
            print(f"Workflow error: {e}")
            return {"workflow_id": workflow_id,
                "status": "error",
                "error": str(e)}

@app.post("/workflow/run")
async def run_workflow():
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    searcher = SmartSearch(db_manager)
    runner = WorkflowRunner(db_manager, searcher)
    url = "https://en.wikisource.org/wiki/The_Gates_of_Morning/Book_1/Chapter_1"
    result = await runner.run_full_pipeline(url)
    
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0",port=8000)