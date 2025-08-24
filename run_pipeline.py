import asyncio
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0,project_root)

from fastapi_server.chromadb_utils import ChromaDBManager
from fastapi_server.main import WorkflowRunner, SmartSearch


async def run_pipeline_and_store():
    db = ChromaDBManager(collection_name="content_versions")
    searcher = SmartSearch(db)
    runner = WorkflowRunner(db, searcher)
    url = "https://en.wikisource.org/wiki/The_Gates_of_Morning/Book_1/Chapter_1"
    result = await runner.run_full_pipeline(url)
    print("Workflow run completed:")
    print(result)

if __name__=='__main__':
    asyncio.run(run_pipeline_and_store())
