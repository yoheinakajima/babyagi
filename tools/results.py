#!/usr/bin/env python3
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import argparse
import openai
import pinecone
from dotenv import load_dotenv
from components.context_storage.IContextStorage import ContextStorage

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
assert OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"

# Context Storage config
TASK_STORAGE_NAME = os.getenv("TASK_STORAGE_NAME", os.getenv("TABLE_NAME", "tasks"))
CONTEXT_STORAGE_TYPE = os.getenv("CONTEXT_STORAGE_TYPE", "pinecone").lower()
context_storage_options = {}

# Pinecone config
if CONTEXT_STORAGE_TYPE == "pinecone":
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")

    assert PINECONE_API_KEY, "PINECONE_API_KEY is missing from .env"
    assert PINECONE_ENVIRONMENT, "PINECONE_ENVIRONMENT is missing from .env"

    def get_ada_embedding(text):
        text = text.replace("\n", " ")
        return openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]

    from components.context_storage.IContextStorage import PineconeOptions
    context_storage_options = PineconeOptions(PINECONE_API_KEY, PINECONE_ENVIRONMENT, get_ada_embedding, TASK_STORAGE_NAME)

# Weaviate config
elif CONTEXT_STORAGE_TYPE == "weaviate":
    WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "")
    WEAVIATE_VECTORIZER = os.getenv("WEAVIATE_VECTORIZER", "")

    assert WEAVIATE_HOST, "WEAVIATE_HOST is missing from .env"
    assert WEAVIATE_VECTORIZER, "WEAVIATE_VECTORIZER is missing from .env"

    from components.context_storage.IContextStorage import WeaviateOptions
    context_storage_options = WeaviateOptions(WEAVIATE_HOST, WEAVIATE_VECTORIZER, TASK_STORAGE_NAME)

else:
    raise Exception("CONTEXT_STORAGE_TYPE must be a valid option (pinecone | weaviate)")

# Function to query records from the Pinecone index
def query_records(index: ContextStorage, query, top_k=1000):
    results = index.query(query, n=top_k)
    return [f"{task.data['task']}:\n{task.data['result']}\n------------------" for task in results]

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Query Pinecone index using a string.")
    parser.add_argument('objective', nargs='*', metavar='<objective>', help='''
    main objective description. Doesn\'t need to be quoted.
    if not specified, get objective from environment.
    ''', default=[os.getenv("OBJECTIVE", "")])
    args = parser.parse_args()

    # Initialize Pinecone
    index = ContextStorage.factory(CONTEXT_STORAGE_TYPE, context_storage_options)

    # Query records from the index
    query = ' '.join(args.objective).strip()
    retrieved_tasks = query_records(index, query)
    for r in retrieved_tasks:
        print(r)

if __name__ == "__main__":
    main()
