import os
import glob
import pickle
from typing import List

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.neighbors import NearestNeighbors
    import numpy as np
except Exception:
    # When dependencies are missing, the module will still import but retrieval will be a no-op.
    SentenceTransformer = None
    NearestNeighbors = None
    np = None

BASE_DIR = os.path.dirname(__file__)
KNOWLEDGE_DIR = os.path.join(BASE_DIR, 'knowledge')
INDEX_FILE = os.path.join(BASE_DIR, 'rag_index.pkl')

MODEL_NAME = 'paraphrase-MiniLM-L6-v2'

class RAGIndex:
    def __init__(self):
        self.model = None
        self.docs: List[str] = []
        self.embeddings = None
        self.nn = None

    def available(self):
        return SentenceTransformer is not None and NearestNeighbors is not None

    def build(self):
        if not self.available():
            return False

        # Load model
        self.model = SentenceTransformer(MODEL_NAME)

        # Read plain text files under knowledge/
        docs = []
        if os.path.isdir(KNOWLEDGE_DIR):
            for path in glob.glob(os.path.join(KNOWLEDGE_DIR, '*.txt')):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        text = f.read().strip()
                        if text:
                            docs.append(text)
                except Exception:
                    continue

        # Fall back to a small default doc if none found
        if not docs:
            docs = [
                "General dairy farming best practices: maintain hygiene, provide clean water, balanced feed, monitor udder health, vaccinate regularly.",
                "Mastitis management: isolate affected animal, consult vet, sample milk for culture, follow recommended antibiotic regimen based on sensitivity testing." 
            ]

        self.docs = docs
        # Compute embeddings
        embs = self.model.encode(docs, show_progress_bar=False, convert_to_numpy=True)
        self.embeddings = embs

        # Build nearest-neighbors index
        self.nn = NearestNeighbors(n_neighbors=min(5, len(docs)), metric='cosine')
        self.nn.fit(embs)

        # Persist index
        try:
            with open(INDEX_FILE, 'wb') as f:
                pickle.dump({'docs': self.docs, 'embeddings': self.embeddings}, f)
        except Exception:
            pass

        return True

    def load(self):
        if not self.available():
            return False

        # Try load from disk
        if os.path.exists(INDEX_FILE):
            try:
                with open(INDEX_FILE, 'rb') as f:
                    data = pickle.load(f)
                    self.docs = data.get('docs', [])
                    self.embeddings = data.get('embeddings', None)
            except Exception:
                self.docs = []
                self.embeddings = None

        # If embeddings not available, build from scratch
        if not self.embeddings:
            return self.build()

        # Load model and nn
        self.model = SentenceTransformer(MODEL_NAME)
        self.nn = NearestNeighbors(n_neighbors=min(5, len(self.docs)), metric='cosine')
        self.nn.fit(self.embeddings)
        return True

    def retrieve(self, query: str, k: int = 3):
        if not self.available():
            return []
        if not self.model or self.embeddings is None:
            if not self.load():
                return []

        q_emb = self.model.encode([query], convert_to_numpy=True)
        distances, indices = self.nn.kneighbors(q_emb, n_neighbors=min(k, len(self.docs)))
        results = []
        for idx in indices[0]:
            results.append(self.docs[idx])
        return results


# Create a global index instance
index = RAGIndex()

def ensure_index():
    try:
        return index.load()
    except Exception:
        try:
            return index.build()
        except Exception:
            return False

def retrieve(query: str, k: int = 3):
    try:
        ok = ensure_index()
        if not ok:
            return []
        return index.retrieve(query, k)
    except Exception:
        return []
