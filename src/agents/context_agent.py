from utils.embedding import get_ada_embedding
from .base_agent import BaseAgent
import pinecone
from typing import Dict, List

class ContextAgent(BaseAgent):
    def __init__(self, config: Dict, index: str, n: int = 5):
        """
        Initialize a ContextAgent instance with its configuration.

        :param config: A dictionary containing agent configuration.
        :param index: The name of the Pinecone index.
        :param n: Number of top tasks to retrieve.
        """
        super().__init__(config)
        self.index = index
        self.n = n

    def get_relevant_tasks(self, query: str, n: int) -> List[str]:
        """
        Retrieve relevant tasks using Pinecone.

        :param query: Input query for context tasks.
        :return: List of relevant tasks.
        """
        query_embedding = get_ada_embedding(query)
        results = self._pinecone_query(query_embedding)

        return self._extract_task_list(results)

    def _pinecone_query(self, query_embedding: List[float]) -> pinecone.FetchResult:
        """
        Perform a Pinecone query.

        :param query_embedding: The query embedding.
        :return: The Pinecone FetchResult object.
        """
        index = pinecone.Index(index_name=self.index)
        return index.query(query_embedding, top_k=self.n, include_metadata=True)

    @staticmethod
    def _extract_task_list(results: pinecone.FetchResult) -> List[str]:
        """
        Extract the task list from the Pinecone FetchResult object.

        :param results: The Pinecone FetchResult object.
        :return: A list of relevant tasks.
        """
        sorted_results = sorted(results.matches, key=lambda x: x.score, reverse=True)
        return [str(item.metadata['task']) for item in sorted_results]