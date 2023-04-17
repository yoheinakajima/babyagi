from memories.base import Memory, MemoryQueryResult, get_ada_embedding
import numpy as np


class NumpyMemory(Memory):
    def __init__(self, vectors=None, ids=None, metadata=None):
        self.vectors = vectors
        self.ids = ids
        self.metadata = metadata

    def query(self, query: str, top_k: int) -> list:
        if self.vectors is None:
            return []
        if isinstance(self.vectors, list) and len(self.vectors) > 1:
            self.vectors = np.vstack(self.vectors)

        n = min(self.vectors.shape[0], top_k)
        query_vector = get_ada_embedding(query)
        similarities = self.vectors @ query_vector
        indices = np.argpartition(similarities, -n)[-n:]
        return [
            MemoryQueryResult(
                self.ids[i],
                similarities[i],
                self.metadata[i]
            )
            for i in indices
        ]

    def add(self, vector_id: str, text: str, metadata: dict) -> None:
        if isinstance(self.vectors, list) and len(self.vectors) > 1:
            self.vectors = np.vstack(self.vectors)

        if self.vectors is None:
            self.vectors = np.array(get_ada_embedding(text)).reshape((1, -1))
            self.ids = [vector_id]
            self.metadata = [metadata]
        else:
            self.ids.append(vector_id)
            self.vectors = np.vstack([self.vectors, np.array(get_ada_embedding(text))])
            self.metadata.append(metadata)

