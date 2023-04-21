#!/usr/bin/env python3
import os
import argparse
import openai
import pinecone
from config.config import Config

config = Config()

# Function to query records from the Pinecone index
def query_records(index, query, top_k=1000):
    results = index.query(query, top_k=top_k, include_metadata=True)
    return [f"{task.metadata['task']}:\n{task.metadata['result']}\n------------------" for task in results.matches]

# Get embedding for the text
def get_ada_embedding(text):
    text = text.replace("\n", " ")
    return openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Query Pinecone index using a string.")
    parser.add_argument('objective', nargs='*', metavar='<objective>', help='''
    main objective description. Doesn\'t need to be quoted.
    if not specified, get objective from environment.
    ''', default=[config.objective])
    args = parser.parse_args()

    # Initialize Pinecone
    pinecone.init(api_key=config.pinecone_api_key)

    # Connect to the objective index
    index = pinecone.Index(config.pinecone_table_name)

    # Query records from the index
    query = get_ada_embedding(' '.join(args.objective).strip())
    retrieved_tasks = query_records(index, query)
    for r in retrieved_tasks:
        print(r)

if __name__ == "__main__":
    main()
