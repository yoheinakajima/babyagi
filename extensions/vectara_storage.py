from typing import Dict, List, Any
import os
import logging
import requests
import json

class VectaraResultsStorage:
    def __init__(self, vectara_api_key: str, vectara_customer_id: str, vectara_corpus_id: str):
        self._vectara_customer_id = vectara_customer_id
        self._vectara_corpus_id = vectara_corpus_id
        self._vectara_api_key = vectara_api_key

        self._vectara_customer_id = vectara_customer_id or os.environ.get("VECTARA_CUSTOMER_ID")
        self._vectara_corpus_id = vectara_corpus_id or os.environ.get("VECTARA_CORPUS_ID")
        self._vectara_api_key = vectara_api_key or os.environ.get("VECTARA_API_KEY")
        if (
            self._vectara_customer_id is None
            or self._vectara_corpus_id is None
            or self._vectara_api_key is None
        ):
            logging.warning(
                "Cant find Vectara credentials, customer_id or corpus_id in "
                "environment."
            )
        else:
            logging.debug(f"Using corpus id {self._vectara_corpus_id}")
        self._session = requests.Session()  # to reuse connections

    def _get_post_headers(self) -> dict:
        """Returns headers that should be attached to each post request."""
        return {
            "x-api-key": self._vectara_api_key,
            "customer-id": self._vectara_customer_id,
            "Content-Type": "application/json",
        }

    def _delete_doc(self, doc_id: str) -> bool:
        """
        Delete a document from the Vectara corpus.

        Args:
            url (str): URL of the page to delete.
            doc_id (str): ID of the document to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        body = {
            "customer_id": self._vectara_customer_id,
            "corpus_id": self._vectara_corpus_id,
            "document_id": doc_id,
        }
        response = self._session.post(
            "https://api.vectara.io/v1/delete-doc",
            data=json.dumps(body),
            verify=True,
            headers=self._get_post_headers(),
        )
        if response.status_code != 200:
            logging.error(
                f"Delete request failed for doc_id = {doc_id} with status code "
                f"{response.status_code}, reason {response.reason}, text "
                f"{response.text}"
            )
            return False
        return True

    def _index_doc(self, doc_id: str, text: str, metadata: dict) -> bool:
        request: dict[str, Any] = {}
        request["customer_id"] = self._vectara_customer_id
        request["corpus_id"] = self._vectara_corpus_id
        request["document"] = {
            "document_id": doc_id,
            "metadataJson": json.dumps(metadata),
            "section": [{"text": text, "metadataJson": json.dumps(metadata)}],
        }

        response = self._session.post(
            headers=self._get_post_headers(),
            url="https://api.vectara.io/v1/index",
            data=json.dumps(request),
            timeout=30,
            verify=True,
        )

        status_code = response.status_code

        result = response.json()
        status_str = result["status"]["code"] if "status" in result else None
        if status_code == 409 or (status_str and status_str == "ALREADY_EXISTS"):
            return False
        else:
            return True


    def add(self, task: Dict, result: str, result_id: int):
        doc_id = result_id
        succeeded = self._index_doc(doc_id, result, {})
        if not succeeded:
            self._delete_doc(doc_id)
            self._index_doc(doc_id, result, {})

    def query(self, query: str, top_results_num: int) -> List[dict]:
        data = json.dumps(
            {
                "query": [
                    {
                        "query": query,
                        "start": 0,
                        "num_results": top_results_num,
                        "context_config": {
                            "sentences_before": 3,
                            "sentences_after": 3,
                        },
                        "corpus_key": [
                            {
                                "customer_id": self._vectara_customer_id,
                                "corpus_id": self._vectara_corpus_id,
                                "lexical_interpolation_config": {"lambda": 0.025},
                            }
                        ],
                    }
                ]
            }
        )

        response = self._session.post(
            headers=self._get_post_headers(),
            url="https://api.vectara.io/v1/query",
            data=data,
            timeout=10,
        )

        if response.status_code != 200:
            logging.error(
                "Query failed %s",
                f"(code {response.status_code}, reason {response.reason}, details "
                f"{response.text})",
            )
            return []

        result = response.json()
        responses = result["responseSet"][0]["response"]
        return [x["text"] for x in responses]
