import importlib
import numpy as np
from typing import Dict, List

import openai
import tair
from tair.tairvector import DistanceMetric, IndexType


def can_import(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


assert can_import("tair"), (
        "\033[91m\033[1m"
        + "tair storage requires package tair-client.\nInstall:  pip install -r extensions/requirements.txt"
)


class TairResultsStorage:
    def __init__(
            self,
            openai_api_key: str,
            tair_host: str,
            tair_port: int,
            tair_username: str,
            tair_password: str,
            llm_model: str,
            llama_model_path: str,
            results_store_name: str,
            objective: str,
            mock_embedding: bool = False):
        openai.api_key = openai_api_key
        self.llm_model = llm_model
        self.llama_model_path = llama_model_path
        self.tair_index_name = results_store_name
        self.dimension = 1536 if not self.llm_model.startswith("llama") else 5120
        self.indextype = IndexType.HNSW
        self.distance_metric = DistanceMetric.InnerProduct
        self.mock_embedding = mock_embedding
        try:
            self.client = tair.Tair(host=tair_host, port=tair_port, username=tair_username, password=tair_password)
        except Exception as e:
            raise e
        ret = self.client.tvs_get_index(self.tair_index_name)
        if ret is None:
            self.client.tvs_create_index(self.tair_index_name, self.dimension, self.distance_metric, self.indextype)

    def add(self, task: Dict, result: str, result_id: int) -> int:
        """
        Takes in a task and result and inserts them into the database.
        Return insert attrs count
        """
        embedding = self._get_embedding(result)
        attrs = {"task": task["task_name"], "result": result}
        self.client.tvs_hset(self.tair_index_name, result_id, vector=embedding, **attrs)

    def query(self, query: str, top_results_num: int) -> List[dict]:
        """
        Takes in query and top_results_num
        Returns a list of query results based on scores.
        """
        embedding = self._get_embedding(query)
        ann_results = self.client.tvs_knnsearch(self.tair_index_name, top_results_num, embedding)
        tasks = list()
        for key, score in ann_results:
            tasks.append(self._try_get(key)["task"])
        return tasks

    def delete_index(self):
        self.client.tvs_del_index(self.tair_index_name)

    def key_exist(self, key) -> bool:
        return self._try_get(key) is not None

    def _try_get(self, key) -> dict:
        return self.client.tvs_hgetall(self.tair_index_name, key)

    def _get_embedding(self, text: str) -> list:
        """
        Get embedding for the text
        """
        if self.mock_embedding:
            vec = np.array([0] * self.dimension).astype(np.float64).tolist()
            vec[hash(text) % self.dimension] = 1
            return vec

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
