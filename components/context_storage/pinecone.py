from .IContextStorage import ContextStorage, PineconeOptions, ContextResult, ContextData
import pinecone

class PineconeTaskStorage(ContextStorage):
    def __init__(self, options: PineconeOptions):
        pinecone.init(api_key=options.api_key, environment=options.environment)
        self.storage_name = options.storage_name
        self._create_storage(options.clean_storage)
        self.embedding_method = options.embedding_method
        self.index = pinecone.Index(options.storage_name)

    def _create_storage(self, clean_storage: bool = False) -> None:
        if self._has_storage():
            if not clean_storage:
                return
            self.delete_storage()
        print(f'(pinecone): creating storage index {self.storage_name}')
        pinecone.create_index(self.storage_name, 1536)
        
    def _has_storage(self) -> bool:
        return self.storage_name in pinecone.list_indexes()
    
    def delete_storage(self) -> None:
        print(f'(pinecone): deleting storage index {self.storage_name}')
        pinecone.delete_index(self.storage_name)
    
    def query(self, query: str, fields: list[str] = None, n: int = 1, namespace: str = 'default') -> list[ContextResult]:
        # Generate query embedding
        query_embedding = self.embedding_method(query)

        # Perform search and retrieve results
        results = self.index.query(query_embedding, top_k=n, namespace=namespace, include_metadata=True)
        sorted_results = sorted(results.get('matches', []), key=lambda x: x.score, reverse=True)

        # Transform results into standard format
        transformed_results = []
        for item in sorted_results:
            data = item['metadata']

            # Filter metadata by fields if specified
            if fields is not None:
                data = { key: value for key, value in data.items() if key in fields }

            # Append transformed result to list
            transformed_results.append(ContextResult(item['id'], item['score'], data))

        return transformed_results
    
    def upsert(self, context: ContextData, namespace: str = 'default') -> None:
        vector = self.embedding_method(context.enriched_data)
        self.index.upsert([(context.id, vector, context.data)], namespace)
