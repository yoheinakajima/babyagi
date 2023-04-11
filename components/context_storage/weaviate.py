import os
from typing import Optional
from .IContextStorage import ContextStorage, ContextResult, ContextData, StorageOptions

class WeaviateOptions(StorageOptions):
    host: str
    vectorizer: str
    storage_name: str
    clean_storage: bool 
    def __init__(
            self, 
            host: Optional[str] = None, 
            vectorizer: Optional[str] = None,
            storage_name: Optional[str] = None,
            clean_storage: bool = False
        ) -> None:

        self.host = os.getenv("WEAVIATE_HOST", "http://localhost:8080") if host is None else host
        self.vectorizer = os.getenv("WEAVIATE_VECTORIZER", "text2vec-transformers") if vectorizer is None else vectorizer
        self.storage_name = os.getenv("WEAVIATE_STORAGE_NAME", "tasks") if storage_name is None else storage_name
        self.clean_storage = clean_storage


class WeaviateTaskStorage(ContextStorage):
    def __init__(self, options: WeaviateOptions = WeaviateOptions()):
        try:
            import weaviate
        except ImportError:
            raise ImportError("Please install weaviate python client: pip install weaviate-client")

        self.client = weaviate.Client(options.host)
        self._create_storage(options.storage_name, options.vectorizer, options.clean_storage)
        self.storage_name = self.client.schema.get(options.storage_name)['class']

    def _create_storage(self, storage_name: str, vectorizer: str, clean_storage: bool = False) -> None:
        if self._has_storage(storage_name):
            if not clean_storage:
                return
            self.delete_storage()
        print(f'(weaviate): creating storage class {storage_name}')
        self.client.schema.create({
            'classes': [{
                'class': storage_name,
                'vectorizer': vectorizer,
            }]
        })
        
    def _has_storage(self, storage_name: str) -> bool:
        existing_classes = [cls['class'].lower() for cls in self.client.schema.get()['classes']]
        return storage_name.lower() in existing_classes
    
    def delete_storage(self) -> None:
        print(f'(weaviate): deleting storage class {self.storage_name}')
        self.client.schema.delete_class(self.storage_name)
    
    def query(self, query: str, fields: list[str] = [], n: int = 1, namespace: str = None) -> list[ContextResult]:
        # If no fields are provided, retrieve the schema and set fields to be all properties in the schema
        if not fields:
            schema = self.client.schema.get(self.storage_name)
            fields = [prop['name'] for prop in schema['properties']]

        # Create query builder with parameters
        query_builder = (
            self.client.query
                .get(self.storage_name, fields)
                .with_near_text({ 'concepts': query })
                .with_limit(n)
                .with_additional(['id', 'certainty'])
        )

        # Limit search by namespace if provided
        if namespace:
            query_builder = query_builder.with_where({ 'path': ['namespace'], 'operator': 'Equal', 'valueText': namespace })

        results = (
            query_builder
                .do()
                .get('data', {})
                .get('Get', {})
                .get(self.storage_name, [])
        )

        # Transform results into standard format
        transformed_results = []
        if results:
            for result in results:
                item = dict(result)

                # Extract additional metadata
                metadata = item.pop('_additional', {})
                id = item.get('context-id', metadata.get('id', 'not-set'))
                
                # Append transformed result to list
                transformed_results.append(ContextResult(id, metadata['certainty'], item))

        return transformed_results
    
    def upsert(self, context: ContextData, namespace: str = 'default') -> None:
        context.data['enriched_data'] = context.enriched_data
        context.data['context_id'] = context.id
        context.data['namespace'] = namespace
        self.client.data_object.create(context.data, self.storage_name)
