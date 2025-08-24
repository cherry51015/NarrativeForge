import chromadb
import uuid
import os
from datetime import datetime

class ChromaDBManager:
    def __init__(self, collection_name="content_versions"):
        try:
            db_path = os.path.join(os.path.dirname(__file__), "..", "data", "chromadb")
            os.makedirs(db_path, exist_ok=True)
            self.client = chromadb.PersistentClient(path=db_path)
            
            try:
                self.collection = self.client.get_collection(collection_name)
                count = self.collection.count()
                print(f"Connected to existing collection: {collection_name} with {count} documents")
            except:
                self.collection = self.client.create_collection(collection_name)
                print(f"Created new collection: {collection_name}")
                
        except Exception as e:
            print(f"Failed to initialize ChromaDB: {e}")
            raise

    def store_version(self, content, role, metadata=None):
        try:
            version_id = f"{role}_{uuid.uuid4().hex[:6]}_{datetime.now().strftime('%H%M')}"
            meta = {
                "role": role,
                "timestamp": datetime.utcnow().isoformat(),
                "version_id": version_id,
                **(metadata or {})
            }
            
            self.collection.add(
                documents=[content],
                metadatas=[meta],
                ids=[version_id]
            )
            print(f"Stored content with ID: {version_id}")
            return version_id
        except Exception as e:
            print(f"Failed to store version: {e}")
            return None

    def search(self, query, limit=5):
        try:
            # First check if collection has any documents
            count = self.collection.count()
            print(f"Collection has {count} documents")
            
            if count == 0:
                print("No documents in collection to search")
                return []
            
            res = self.collection.query(query_texts=[query], n_results=min(limit, count))
            docs = res["documents"][0] if res["documents"] else []
            metas = res.get("metadatas", [[]])[0]
            dists = res.get("distances", [[]])[0]
            
            results = []
            for i, (doc, meta) in enumerate(zip(docs, metas)):
                score = 1 - dists[i] if i < len(dists) else 0.5
                result = {
                    "content": doc[:200] + "..." if len(doc) > 200 else doc,
                    "role": meta.get("role", ""),
                    "version_id": meta.get("version_id", ""),
                    "score": score,
                    "timestamp": meta.get("timestamp", ""),
                    "type": meta.get("type", "")
                }
                results.append(result)
            
            print(f"Search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            print(f"Search failed: {e}")
            return []
    
    def get_all_documents(self):
        try:
            count = self.collection.count()
            if count == 0:
                return {"count": 0, "documents": [], "metadatas": [], "ids": []}
            res = self.collection.get()
            return {
                "count": count,
                "documents": res.get("documents", []),
                "metadatas": res.get("metadatas", []),
                "ids": res.get("ids", [])
            }
        except Exception as e:
            print(f"Failed to get all documents: {e}")
            return {"count": 0, "documents": [], "metadatas": [], "ids": []}
    
    def clear_collection(self):
        try:
            collection_name =self.collection.name
            self.client.delete_collection(collection_name)
            self.collection = self.client.create_collection(collection_name)
            print(f"Cleared collection:{collection_name}")
            return True
        except Exception as e:
            print(f"Failed to clear collection:{e}")
            return False