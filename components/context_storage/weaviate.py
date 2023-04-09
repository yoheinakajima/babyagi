from .IContextStorage import ContextStorage, WeaviateOptions, ContextResult, ContextData
import weaviate

class WeaviateTaskStorage(ContextStorage):
    def __init__(self, options: WeaviateOptions):
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
    
    def query(self, query: str, fields: list[str] = [], n: int = 1) -> list[ContextResult]:
        # If no fields are provided, retrieve the schema and set fields to be all properties in the schema
        if not fields:
            schema = self.client.schema.get(self.storage_name)
            fields = [prop['name'] for prop in schema['properties']]
        
        # Perform search and retrieve results
        results = (
            self.client.query
                .get(self.storage_name, fields)
                .with_near_text({ 'concepts': query })
                .with_limit(n)
                .with_additional(['id', 'certainty'])
                .do()
                .get('data', {})
                .get('Get', {})
                .get(self.storage_name, [])
        )

        # Transform results into standard format
        transformed_results = []
        for result in results:
            item = dict(result)

            # Extract additional metadata
            metadata = item.pop('_additional', {})
            
            # Append transformed result to list
            transformed_results.append(ContextResult(metadata['id'], metadata['certainty'], item))

        return transformed_results
    
    def upsert(self, context: ContextData) -> None:
        context.data['enriched_data'] = context.enriched_data
        context.data['id'] = context.id
        self.client.data_object.create(context.data, self.storage_name)