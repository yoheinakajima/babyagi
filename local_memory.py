import numpy as np
import os
import json
from scipy.spatial.distance import cdist


class EmbeddingSearchResult:
    def __init__(self, item, score, metadata=None):
        self.item = item
        self.score = score
        self.metadata = metadata

class EmbeddingSearchResults:
    def __init__(self, matches):
        self.matches = matches


class LocalMemory:
    def __init__(self, botname, resume):
        self.words = []
        self.embeddings = []
        self.metadata = []
        self.memfile = f'memory/{botname}_memory.json'
        if resume:
            self.load_memory()
        
    def load_memory(self):
        if os.path.exists(self.memfile):
            with open(self.memfile, 'r') as f:
                memory_data = json.load(f)
                self.embeddings = memory_data["embeddings"]
                self.words = memory_data["words"]
                self.metadata = memory_data["metadata"]

    def add_embedding(self, word, embedding, metadata=None):
        self.words.append(word)
        self.embeddings.append(embedding)
        self.metadata.append(metadata)
        
        if not os.path.exists("memory"):
            os.makedirs("memory")
        
        memory_data = {
            "embeddings": self.embeddings,
            "words": self.words,
            "metadata": self.metadata,
        }
        with open(self.memfile, "w") as f:
            json.dump(memory_data, f)

    def find_closest_matches(self, embedding, k=5):
        if not self.embeddings:
            return []
        
        embeddings_2d = np.array(self.embeddings).reshape(len(self.embeddings), -1)
        distances = cdist(np.array([embedding]).reshape(1, len(embedding)), embeddings_2d, metric='cosine')
        indices = np.argsort(distances)[0][:k]
        matches = [(self.words[i], self.metadata[i], distances[0][i]) for i in indices]
        return matches


    def query(self, embedding, top_k=10, include_metadata=False, namespace=None):
        matches = self.find_closest_matches(embedding, k=top_k)
        results = []
        for match in matches:
            metadata = {}
            if include_metadata:
                metadata = match[1]
                if namespace is not None and 'namespace' in metadata and metadata['namespace'] != namespace:
                    continue
            results.append(EmbeddingSearchResult(match[0], match[2], metadata))
        return EmbeddingSearchResults(results)

    def upsert(self, embeddings_with_metadata, namespace=None):
        for result_id, embedding, metadata in embeddings_with_metadata:
            self.add_embedding(result_id, embedding, metadata)
            if namespace is not None and metadata is not None:
                metadata['namespace'] = namespace
