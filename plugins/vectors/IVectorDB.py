from abc import ABC, abstractmethod

class VectorDB(ABC):
    @abstractmethod
    def create_table(self, name: str, vectorizer: str) -> bool:
        pass

    @abstractmethod
    def delete_table(self, name: str) -> bool:
        pass

    @abstractmethod
    def has_table(self, name: str) -> bool:
        pass

    @abstractmethod
    def query_table(self, query: str, table_name: str, n: int) -> list:
        pass

    @abstractmethod
    def insert_data(self, data: dict) -> None:
        pass

def get_vector_client(vector_type: str, host: str, table_name: str) -> VectorDB:
    if vector_type.upper() == "WEAVIATE":
        from plugins.vectors.weaviate import Weaviate
        return Weaviate(host, table_name)
    # if vector_type.upper() == "PINECONE":
    #     from plugins.vectors.pinecone import Pinecone
    #     return Pinecone(host, environment, table_name)
    return None