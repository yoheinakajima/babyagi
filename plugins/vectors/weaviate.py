from .IVectorDB import VectorDB
from ..agents.IAgent import Task
import weaviate

class Weaviate(VectorDB):
    def __init__(self, host: str = "http://localhost:8080", table_name: str = "tasks"):
        self.client = weaviate.Client(host)
        self.table_name = table_name
        self.create_table(table_name)

    def create_table(self, name: str, vectorizer: str = "text2vec-transformers") -> bool:
        if(not self.has_table(name)):
            self.client.schema.create({
                "classes": [{
                    "class": name,
                    "vectorizer": vectorizer,
                    "vectorIndexType": "hnsw",
                    "vectorIndexConfig": {
                        "distance": "cosine",
                        "ef": 150, # -1
                        "efConstruction": 150, # 128
                        "maxConnections": 25 # 64
                    }
                }]
            })
            return True
        return False

    def delete_table(self, name: str) -> bool:
        if(self.has_table(name)):
            self.client.schema.delete_class(name)
            return True
        return False

    def has_table(self, name: str) -> bool:
        existing_classes = [cls['class'].lower() for cls in self.client.schema.get()['classes']]
        if(name.lower() in existing_classes):
            return True
        return False

    def query_table(self, query: str, table_name: str = "", n: int = 1) -> list:
        if(not table_name):
            table_name = self.table_name
        results = (
            self.client.query
                .get(table_name, ["task", "result"])
                .with_near_text({ "concepts": [query]})
                .with_limit(n)
                .do()    
                .get("data", {})
                .get("Get", {})
                .get(table_name, [])
        )
        return [str(item["task"]) for item in results]

    def insert_data(self, task: Task) -> None:
        self.client.data_object.create({'task': task.description, 'result': task.result}, self.table_name)
