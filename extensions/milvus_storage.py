import importlib
from typing import List, Dict

import pymilvus
import openai


def can_import(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


assert (
    can_import("pymilvus")
), "\033[91m\033[1m"+"Milvus storage requires package pymilvus.\nInstall:  pip install -r extensions/requirements.txt"


class MilvusResultsStorage:
    def __init__(
        self,
        openai_api_key: str,
        llm_model: str,
        llama_model_path: str,
        uri: str,
        collection_name: str,
        vector_field: str,
        **kws
    ):
        openai.api_key = openai_api_key

        self.llm_model = llm_model
        self.llama_model_path = llama_model_path

        self.vector_field = vector_field
        self._milvus_client = pymilvus.MilvusClient(
            collection_name=collection_name,
            vector_field=vector_field,
            uri=uri,
            **kws
        )

    def get_embedding(self, text: str) -> List:
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

    def add(self, task: Dict, result: str, result_id: str, **kws):
        # Add task and result into meta when meta is supported
        data = {
            "task": task["task_name"],
            "result_id": result_id,
            "result": result,
            self.vector_field: self.get_embedding(result)
        }

        self._milvus_client.insert_data(data=[data], **kws)

    def query(self, query: str, top_results_num: int, **kws) -> List[dict]:
        query_embedding = self.get_embedding(query)
        results = self._milvus_client.search_data(query_embedding, top_k=top_results_num, return_fields=["task"], **kws)[0]
        return [item["data"]["task"] for item in results]
