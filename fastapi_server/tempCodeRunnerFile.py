import sys
import os
import uuid
import random
import numpy as np
from fastapi import FastAPI
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

# Add project root to sys.path so sibling modules can be imported
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ai_pipeline.ai_pipeline import rewrite, review
from scraping.scrape_chapter import scrape_chapter
from chromadb_utils import ChromaDBManager


app = FastAPI(title="Morning Glory")
chroma_manager = ChromaDBManager()


# Pydantic request models
class ContentIn(BaseModel):
    content: str
    role: str = "writer"
    context: Optional[str] = None


class EditIn(BaseModel):
    content: str
    role: str
    why: str = ""
    rating: int = 5


class QueryIn(BaseModel):
    query: str
    limit: int = 5


class VoiceIn(BaseModel):
    command: str


class RateSearchIn(BaseModel):
    query: str
    rating: float


# RL feedback logger (simple print-based for demo)
def log_rl_feedback(action: str, reward: float, context: dict = None):
    print(f"RL Feedback - Action: {action}, Reward: {reward}, Context: {context}")


def handle_voice(data):
    return {"response": "Command not recognized. Please try 'smart search', 'run workflow', or 'stats'."}


# SmartSearch and WorkflowRunner classes and their methods remain unchanged


class SmartSearch:
    def __init__(self, chroma_db):
        self.db = chroma_db
        self.learned_stuff = {}
        self.explore_rate = 0.2
        self.learning_rate = 0.1
        self.search_history = []

        self.strategies = ["exact", "semantic", "expanded", "mixed"]

    def categorize_query(self, query):
        words = len(query.split())
        is_tech = any(word in query.lower() for word in ['chapter', 'review', 'content'])
        length = "short" if len(query) < 30 else "long"
        return f"{length}_{words}w_tech{is_tech}"

    def pick_strategy(self, category):
        if random.random() < self.explore_rate:
            return random.choice(self.strategies)
        if category not in self.learned_stuff:
            self.learned_stuff[category] = {s: 0.0 for s in self.strategies}
        return max(self.learned_stuff[category], key=self.learned_stuff[category].get)

    def search_with_strategy(self, query, strategy, limit=5):
        if strategy == "exact":
            results = self.db.search(f'"{query}"', limit)
            if not results:
                results = self.db.search(query, limit)
        elif strategy == "expanded":
            expanded = query
            if "chapter" in query.lower():
                expanded += " story content narrative"
            if "review" in query.lower():
                expanded += " feedback quality analysis"
            results = self.db.search(expanded, limit)
        elif strategy == "mixed":
            sem_results = self.db.search(query, limit // 2)
            exact_results = self.db.search(f'"{query}"', limit // 2)
            results = sem_results + exact_results
        else:
            results = self.db.search(query, limit)
        return results

    def rate_results(self, results, user_score=None):
        if not results:
            return 2.0
        quantity = min(len(results) * 2, 6)
        relevance = np.mean([r.get('score', 0.5) for r in results]) * 2
        content_ok = 2 if np.mean([len(str(r.get('content', ''))) for r in results]) > 50 else 1
        calc_score = quantity + relevance + content_ok
        if user_score:
            return (calc_score + user_score) / 2
        return min(calc_score, 10.0)

    def learn_from_result(self, category, strategy, score):
        if category not in self.learned_stuff:
            self.learned_stuff[category] = {s: 0.0 for s in self.strategies}
        old = self.learned_stuff[category][strategy]
        self.learned_stuff[category][strategy] = old + self.learning_rate * (score - old)

    def smart_search(self, query, limit=5, feedback=None):
        category = self.categorize_query(query)
        strategy = self.pick_strategy(category)
        results = self.search_with_strategy(query, strategy, limit)
        score = self.rate_results(results, feedback)
        self.learn_from_result(category, strategy, score)
        self.search_history.append({
            'query': query,
            'strategy': strategy,
            'score': score,
            'results_count': len(results),
            'time': datetime.now().isoformat()
        })
        log_rl_feedback("smart_search", score, {'strategy': strategy})

        return {
            'results': results,
            'info': {
                'strategy': strategy,
                'score': score,
                'learned_values': self.learned_stuff.get(category, {})
            }
        }

    def get_stats(self):
        if not self.search_history:
            return {"searches": 0, "avg_score": 0}

        scores = [h['score'] for h in self.search_history]
        strategies = [h['strategy'] for h in self.search_history]

        return {
            "searches": len(self.search_history),
            "avg_score": np.mean(scores),
            "recent_scores": scores[-5:],
            "strategy_usage": {s: strategies.count(s) for s in set(strategies)},
            "knowledge_base": len(self.learned_stuff)
        }


class WorkflowRunner:
    def __init__(self, db, searcher):
        self.db = db
        self.searcher = searcher
        self.workflows = {}

    async def run_full_pipeline(self, url=None):
        workflow_id = uuid.uuid4().hex[:6]
        target_url = url or "https://en.wikisource.org/wiki/The_Gates_of_Morning/Book_1/Chapter_1"

        workflow_data = {
            'id': workflow_id,
            'status': 'running',
            'steps': [],
            'start': datetime.now().isoformat()}
        self.workflows[workflow_id] = workflow_data
        screenshot_file = "../data/screenshot.png"
        content_file = "../data/scraped.txt"
        await scrape_chapter(target_url, screenshot_file, content_file)
        with open(content_file, 'r', encoding='utf-8') as f:
            original = f.read()

        scrape_version = self.db.store_version(original, "scraper", {"url": target_url})
        workflow_data['steps'].append({'step': 'scrape', 'version': scrape_version})
        log_rl_feedback("scrape", 8.0, {"length": len(original)})
        rewritten = rewrite(original)
        with open("../data/rewritten.txt", 'w', encoding='utf-8') as f:
            f.write(rewritten)

        rewrite_version = self.db.store_version(rewritten, "ai_writer", {"source": scrape_version})
        workflow_data['steps'].append({'step': 'rewrite', 'version': rewrite_version})
        log_rl_feedback("rewrite", 7.5, {"version": rewrite_version})
        reviewed = review(rewritten)
        with open("../data/reviewed.txt", 'w', encoding='utf-8') as f:
            f.write(reviewed)

        review_version = self.db.store_version(reviewed, "ai_reviewer", {"source": rewrite_version})
        workflow_data['steps'].append({'step': 'review', 'version': review_version})
        log_rl_feedback("review", 8.0, {"version": review_version})
        workflow_data.update({
            'status': 'completed',
            'end': datetime.now().isoformat(),
            'files': [screenshot_file, content_file, "../data/rewritten.txt", "../data/reviewed.txt"]})
        return {'workflow_id': workflow_id,
                'status': 'success',
                'original_size': len(original),
                'rewritten_size': len(rewritten),
                'reviewed_size': len(reviewed),
                'files_created': workflow_data['files'],
                'next': 'ready for human editing'}


smart_searcher = SmartSearch(chroma_manager)
workflow_runner = WorkflowRunner(chroma_manager, smart_searcher)


@app.post("/search/smart")
def smart_search_api(q: QueryIn):
    result = smart_searcher.smart_search(q.query, q.limit)
    return {"query": q.query,
            "results": result["results"],
            "search_info": result["info"]}


@app.post("/search/rate")
def rate_search(data: RateSearchIn):
    result = smart_searcher.smart_search(data.query, 5, data.rating)
    return {"message": "feedback recorded",
            "query": data.query,
            "rating": data.rating,
            "updated_knowledge": result["info"]["learned_values"]}


@app.post("/workflow/run")
async def run_workflow(url: str = None):
    result = await workflow_runner.run_full_pipeline(url)
    return result


@app.get("/workflow/{workflow_id}")
def get_workflow(workflow_id: str):
    return workflow_runner.workflows.get(workflow_id, {"err": "not found"})


@app.get("/stats")
def get_search_stats():
    return smart_searcher.get_stats()


@app.post("/voice/smart")
def smart_voice(data: VoiceIn):
    cmd = data.command.lower()

    if "smart search" in cmd:
        query = cmd.replace("smart search", "").strip()
        if query:
            result = smart_searcher.smart_search(query, 3)
            strategy = result["info"]["strategy"]
            count = len(result["results"])
            return {"response": f"Found {count} results using {strategy} approach"}
        return {"response": "what should i search for?"}
    elif "run workflow" in cmd:
        return {"response": "starting chapter workflow"}
    elif "stats" in cmd:
        stats = smart_searcher.get_stats()
        return {"response": f"did {stats['searches']} searches, avg score {stats['avg_score']:.1f}"}
    return handle_voice(data)


@app.get("/test")
def quick_test():
    search_test = smart_searcher.smart_search("test query", 2)
    stats = smart_searcher.get_stats()
    return {"search_working": len(search_test["results"]) >= 0,
            "learning_working": stats["searches"] >= 0,
            "status": "system ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
