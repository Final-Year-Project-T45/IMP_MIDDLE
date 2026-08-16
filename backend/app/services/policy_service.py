import os
import glob
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger("finsecure.policy")

class PolicyKnowledgeBase:
    def __init__(self, policies_dir: str = "policies_data"):
        self.policies_dir = policies_dir
        self.documents: List[Dict[str, str]] = []
        self.vectorizer: TfidfVectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = None
        self.load_and_index_policies()

    def load_and_index_policies(self):
        txt_files = glob.glob(os.path.join(self.policies_dir, "*.txt"))
        if not txt_files:
            # Fallback if relative path is different
            alt_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "policies_data")
            txt_files = glob.glob(os.path.join(alt_path, "*.txt"))

        self.documents = []
        texts = []
        
        for file_path in txt_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    filename = os.path.basename(file_path)
                    doc_title = filename.replace(".txt", "").replace("_", " ").title()
                    
                    # Store whole document & paragraph chunks
                    self.documents.append({
                        "id": filename,
                        "title": doc_title,
                        "content": content,
                        "file_path": file_path
                    })
                    texts.append(f"{doc_title}\n{content}")
            except Exception as e:
                logger.error(f"Error loading policy file {file_path}: {e}")

        if texts:
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
            logger.info(f"Indexed {len(self.documents)} policy documents into vector search engine.")

    def search(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        if not self.documents or self.tfidf_matrix is None:
            return []

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Get top k indices sorted by similarity score
        top_indices = similarities.argsort()[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            doc = self.documents[idx]
            results.append({
                "id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "relevance_score": round(score, 4)
            })
            
        return results

    def list_all_policies(self) -> List[Dict[str, str]]:
        return [{"id": d["id"], "title": d["title"]} for d in self.documents]

# Global Singleton
policy_kb = PolicyKnowledgeBase()
