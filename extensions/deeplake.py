from typing import Dict

import deeplake
from deeplake.constants import MB
import numpy as np
import openai


class DeepLakeStorage:
    def __init__(self, dataset: str, token: str | None, llm_model, llm_model_path):
        """Initialize DeepLake Storage Memory Provider"""
        self.dataset = deeplake.empty(dataset, token=token)
        self.dataset.create_tensor(
            "task",
            htype="text",
            create_id_tensor=False,
            create_sample_info_tensor=False,
            create_shape_tensor=False,
            chunk_compression="lz4",
        )

        self.dataset.create_tensor(
            "result",
            htype="text",
            create_id_tensor=False,
            create_sample_info_tensor=False,
            create_shape_tensor=False,
            chunk_compression="lz4",
        )

        self.dataset.create_tensor(
            "embedding",
            htype="generic",
            dtype=np.float64,
            create_id_tensor=False,
            create_sample_info_tensor=False,
            max_chunk_size=64 * MB,
            create_shape_tensor=True,
        )

        self.llm_model = llm_model
        self.llm_model_path = llm_model_path

    def add(self, task: Dict, result: str, _: int):
        """Add an embedding of data into memory.
        Args:
            data (str): The raw text to construct embedding index.
        Returns:
            str: log.
        """
        # Don't do anything if we already have the result stored
        if result in self.dataset.result:
            return

        embedding = self.get_embedding(result)
        self.dataset.embedding.append(embedding)
        self.dataset.task.append(task["task_name"])
        self.dataset.result.append(result)

    def query(self, query: str, top_results_num=5):
        embedding = self.get_embedding(query)
        embeddings = self.dataset.embedding.numpy(fetch_chunks=True)
        if embeddings.size == 0:
            return []
        scores = np.dot(embeddings, embedding)
        top_k_indices = np.argsort(scores)[-top_results_num:][::-1]

        return [
            self.dataset.task[int(i)].data()["value"]
            for i in top_k_indices
        ]

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
