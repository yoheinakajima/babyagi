# def get_ada_embedding(text):
#     text = text.replace("\n", " ")
#     return openai.Embedding.create(input=[text], model="text-embedding-ada-002")[
#         "data"
#     ][0]["embedding"]
# def context_agent(query: str, n: int):
#     query_embedding = get_ada_embedding(query)
#     results = index.query(query_embedding, top_k=n, include_metadata=True, namespace=OBJECTIVE)
#     # print("***** RESULTS *****")
#     # print(results)
#     sorted_results = sorted(results.matches, key=lambda x: x.score, reverse=True)
#     return [(str(item.metadata["task"])) for item in sorted_results]