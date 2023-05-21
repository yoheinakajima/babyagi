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
    def __init__(self, openai_api_key: str, pinecone_api_key: str, pinecone_environment: str, llm_model: str, llama_model_path: str, results_store_name: str, objective: str):
        openai.api_key = openai_api_key
        pinecone.init(api_key=pinecone_api_key, environment=pinecone_environment)

        # Pinecone namespaces are only compatible with ascii characters (used in query and upsert)
        self.namespace = re.sub(re.compile('[^\x00-\x7F]+'), '', objective)

        self.llm_model = llm_model
        self.llama_model_path = llama_model_path

        results_store_name = results_store_name
        dimension = 1536 if not self.llm_model.startswith("llama") else 5120
        metric = "cosine"
        pod_type = "p1"
        if results_store_name not in pinecone.list_indexes():
            pinecone.create_index(
                results_store_name, dimension=dimension, metric=metric, pod_type=pod_type
            )

        self.index = pinecone.Index(results_store_name)
        index_stats_response = self.index.describe_index_stats()
        assert dimension == index_stats_response['dimension'], "Dimension of the index does not match the dimension of the LLM embedding"

    def add(self, task: Dict, result: str, result_id: int):
        vector = self.get_embedding(
            result
        )
        self.index.upsert(
            [(result_id, vector, {"task": task["task_name"], "result": result})], namespace=self.namespace
        )

    def query(self, query: str, top_results_num: int) -> List[dict]:
        query_embedding = self.get_embedding(query)
        results = self.index.query(query_embedding, top_k=top_results_num, include_metadata=True, namespace=self.namespace)
        sorted_results = sorted(results.matches, key=lambda x: x.score, reverse=True)
        return [(str(item.metadata["task"])) for item in sorted_results]

    # Get embedding for the text
    def get_embedding(self, text: str) -> list:
        text = text.replace("\n", " ")

        if self.llm_model.startswith("llama"):
            from llama_cpp import Llama

            llm_embed = Llama(
                model_path=self.llama_model_path,
                n_ctx=2048, n_threads=4,
                embedding=True, use_mlock=True,
            )
            return llm_embed.embed(text)

        return openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]
