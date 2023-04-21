from typing import Dict, List
import importlib
import openai
import pinecone
import re

def can_import(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

assert (
    can_import("pinecone")
), "\033[91m\033[1m"+"Pinecone storage requires package pinecone-client.\nInstall:  pip install -r extensions/requirements.txt"

class PineconeResultsStorage:
    def __init__(self, openai_api_key: str, pinecone_api_key: str, pinecone_environment: str, table_name: str, objective: str):
        openai.api_key = openai_api_key
        pinecone.init(api_key=pinecone_api_key, environment=pinecone_environment)

        # Pinecone namespaces are only compatible with ascii characters (used in query and upsert)
        self.namespace = re.sub(re.compile('[^\x00-\x7F]+'), '', objective)

        table_name = table_name
        dimension = 1536
        metric = "cosine"
        pod_type = "p1"
        if table_name not in pinecone.list_indexes():
            pinecone.create_index(
                table_name, dimension=dimension, metric=metric, pod_type=pod_type
            )

        self.index = pinecone.Index(table_name)

    def add(self, task: Dict, result: Dict, result_id: int, vector: List):
        enriched_result = {
            "data": result
        }
        vector = self.get_ada_embedding(
            enriched_result["data"]
        )
        self.index.upsert(
            [(result_id, vector, {"task": task["task_name"], "result": result})], namespace=self.namespace
        )

    def query(self, query: str, top_results_num: int) -> List[dict]:
        query_embedding = self.get_ada_embedding(query)
        results = self.index.query(query_embedding, top_k=top_results_num, include_metadata=True, namespace=self.namespace)
        sorted_results = sorted(results.matches, key=lambda x: x.score, reverse=True)
        return [(str(item.metadata["task"])) for item in sorted_results]

    # Get embedding for the text
    def get_ada_embedding(self, text:str) -> list:
        text = text.replace("\n", " ")
        return openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]
