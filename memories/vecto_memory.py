import io

from memories.base import Memory, MemoryQueryResult
import os
import requests
from vecto import vecto_toolbelt
from vecto import Vecto


class VectoMemory(Memory):
    def __init__(self, api_key=None, vector_space=None, initialize=True):
        if api_key is None:
            api_key = os.getenv("VECTO_API_KEY")

        if vector_space is None:
            vector_space = os.getenv("VECTO_VECTOR_SPACE")

        headers = {'Authorization': 'Bearer ' + api_key}
        response = requests.get("https://api.vecto.ai/api/v0/account/space", headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to get vector space list: {response.text}")

        self.vs = None
        for space in response.json():
            if space['name'] == vector_space:
                self.vs = Vecto(api_key, space['id'])
                if initialize:
                    self.vs.delete_vector_space_entries()
        if not self.vs:
            raise Exception(f"Could not find vector space with name {vector_space}")

    def query(self, query: str, top_k: int) -> list:
        return [
            MemoryQueryResult(
                str(result.id),
                result.similarity,
                result.attributes,
            ) for result in self.vs.lookup(io.StringIO(query), 'TEXT', top_k).results
        ]

    def add(self, id: str, text: str, metadata: dict) -> None:
        vecto_toolbelt.ingest_text(self.vs, [text], [metadata])
