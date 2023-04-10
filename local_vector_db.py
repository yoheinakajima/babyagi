import numpy as np

class LocalVectorDB:
    def __init__(self, dimension):
        self.dimension = dimension
        self.vectors = {}
        
    def add_vector(self, id, vector):
        if len(vector) != self.dimension:
            raise ValueError("The length of the vector does not match the expected dimension.")
        self.vectors[id] = vector
    
    def delete_vector(self, id):
        if id not in self.vectors:
            raise ValueError(f"The ID {id} is not found in the database.")
        del self.vectors[id]
    
    def get_vector(self, id):
        if id not in self.vectors:
            raise ValueError(f"The ID {id} is not found in the database.")
        return self.vectors[id]
    
    def query(self, query_vector, top_k=10):
        scores = {}
        for id, vector in self.vectors.items():
            score = np.dot(query_vector, vector) / (np.linalg.norm(query_vector) * np.linalg.norm(vector))
            scores[id] = score
        
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        results = [{"id": id, "score": score} for id, score in sorted_scores]
        return results
