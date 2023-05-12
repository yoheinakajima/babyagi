import importlib
import logging
import re
from typing import Dict, List

import openai
import weaviate
from weaviate.embedded import EmbeddedOptions


def can_import(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


assert can_import("weaviate"), (
    "\033[91m\033[1m"
    + "Weaviate storage requires package weaviate-client.\nInstall:  pip install -r extensions/requirements.txt"
)


def create_client(
    weaviate_url: str, weaviate_api_key: str, weaviate_use_embedded: bool
):
    if weaviate_use_embedded:
        client = weaviate.Client(embedded_options=EmbeddedOptions())
    else:
        auth_config = (
            weaviate.auth.AuthApiKey(api_key=weaviate_api_key)
            if weaviate_api_key
            else None
        )
        client = weaviate.Client(weaviate_url, auth_client_secret=auth_config)

    return client


class WeaviateResultsStorage:
    schema = {
        "properties": [
            {"name": "result_id", "dataType": ["string"]},
            {"name": "task", "dataType": ["string"]},
            {"name": "result", "dataType": ["text"]},
        ]
    }

    def __init__(
        self,
        openai_api_key: str,
        weaviate_url: str,
        weaviate_api_key: str,
        weaviate_use_embedded: bool,
        llm_model: str,
        llama_model_path: str,
        results_store_name: str,
        objective: str,
    ):
        openai.api_key = openai_api_key
        self.client = create_client(
            weaviate_url, weaviate_api_key, weaviate_use_embedded
        )
        self.index_name = None
        self.create_schema(results_store_name)

        self.llm_model = llm_model
        self.llama_model_path = llama_model_path

    def create_schema(self, results_store_name: str):
        valid_class_name = re.compile(r"^[A-Z][a-zA-Z0-9_]*$")
        if not re.match(valid_class_name, results_store_name):
            raise ValueError(
                f"Invalid index name: {results_store_name}. "
                "Index names must start with a capital letter and "
                "contain only alphanumeric characters and underscores."
            )

        self.schema["class"] = results_store_name
        if self.client.schema.contains(self.schema):
            logging.info(
                f"Index named {results_store_name} already exists. Reusing it."
            )
        else:
            logging.info(f"Creating index named {results_store_name}")
            self.client.schema.create_class(self.schema)

        self.index_name = results_store_name

    def add(self, task: Dict, result: Dict, result_id: int, vector: List = None):
        enriched_result = {"data": result}
        if vector is not None:
            vector = self.get_embedding(enriched_result["data"])

        with self.client.batch as batch:
            data_object = {
                "result_id": result_id,
                "task": task["task_name"],
                "result": result,
            }
            batch.add_data_object(
                data_object=data_object, class_name=self.index_name, vector=vector
            )

    def query(self, query: str, top_results_num: int) -> List[dict]:
        query_embedding = self.get_embedding(query)

        results = (
            self.client.query.get(self.index_name, ["task"])
            .with_hybrid(query=query, alpha=0.5, vector=query_embedding)
            .with_limit(top_results_num)
            .do()
        )

        return self._extract_tasks(results)

    def _extract_tasks(self, data):
        task_data = data.get("data", {}).get("Get", {}).get(self.index_name, [])
        return [item["task"] for item in task_data]

    # Get embedding for the text
    def get_embedding(self, text: str) -> list:
        text = text.replace("\n", " ")

        if self.llm_model.startswith("llama"):
            from llama_cpp import Llama

            llm_embed = Llama(
                model_path=self.llama_model_path,
                n_ctx=2048,
                n_threads=4,
                embedding=True,
                use_mlock=True,
            )
            return llm_embed.embed(text)

        return openai.Embedding.create(input=[text], model="text-embedding-ada-002")[
            "data"
        ][0]["embedding"]
