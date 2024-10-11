from functionz.core.framework import func

@func.register_function(
    metadata={
        "name": "generate_and_process_queries",
        "description": "Generates a specified number of synthetic queries based on a user description and processes each query using the choose_or_create_function.",
        "input_parameters": {
            "user_description": "A detailed description provided by the user.",
            "num_queries": "An integer specifying the number of synthetic queries to generate."
        },
        "output": "A dictionary containing the results of each processed query along with intermediate steps and any errors."
    },
    dependencies=[
        "choose_or_create_function",
        "litellm.completion",
    ],
    imports=[
        {"name": "litellm", "lib": "litellm"},
        {"name": "pydantic", "lib": "pydantic"},
        {"name": "typing", "lib": "typing"},
        {"name": "json", "lib": "json"},
    ]
)
def generate_and_process_queries(user_description: str, num_queries: int) -> dict:
    """
    Generates X synthetic queries based on the user description and processes each query
    using the choose_or_create_function.

    Args:
        user_description (str): The user's description to base synthetic queries on.
        num_queries (int): The number of synthetic queries to generate.

    Returns:
        dict: A dictionary containing the results of each query execution, intermediate steps, and any relevant information.
    """
    from litellm import completion
    from pydantic import BaseModel, Field, ValidationError
    from typing import List, Dict, Any
    import json

    intermediate_steps = []
    results = []

    # Step 1: Generate synthetic queries based on the user description
    system_prompt = """
You are an AI assistant specialized in generating relevant and distinct queries based on a given description.

Given a user description, generate a specified number of unique and diverse queries that a user might ask an AI assistant.
Ensure that the queries are varied and cover different aspects of the description.

Return your response in the following JSON format:

{
    "queries": [
        "First synthetic query.",
        "Second synthetic query.",
        ...
    ]
}

Provide only the JSON response, without any additional text.
"""

    class QueryGenerationResponse(BaseModel):
        queries: List[str] = Field(..., description="A list of generated synthetic queries.")

    generation_prompt = f"""
User Description:
\"\"\"{user_description}\"\"\"

Number of Queries to Generate:
{num_queries}
"""

    try:
        generation_response = completion(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": generation_prompt}
            ],
            response_format=QueryGenerationResponse
        )
        print(f"[DEBUG] Generation Response: {generation_response}")
    except Exception as e:
        print(f"[ERROR] LLM call for query generation failed: {e}")
        intermediate_steps.append({"step": "Error in Query Generation LLM Call", "content": str(e)})
        return {"intermediate_steps": intermediate_steps, "error": "# Error generating synthetic queries."}

    # Parse the response
    try:
        content = generation_response.choices[0].message.content
        print(f"[DEBUG] Raw Generation Content: {content}")
        generation_parsed = QueryGenerationResponse.parse_raw(content)
        print(f"[DEBUG] Parsed Query Generation: {generation_parsed}")
        intermediate_steps.append({"step": "Generate Synthetic Queries", "content": generation_parsed.dict()})
    except (ValidationError, IndexError, AttributeError, json.JSONDecodeError) as e:
        print(f"[ERROR] Parsing query generation response failed: {e}")
        intermediate_steps.append({"step": "Error Parsing Query Generation Response", "content": str(e)})
        return {"intermediate_steps": intermediate_steps, "error": "# Error parsing synthetic queries."}

    synthetic_queries = generation_parsed.queries

    if not synthetic_queries or len(synthetic_queries) != num_queries:
        print(f"[ERROR] Number of generated queries does not match the requested number.")
        intermediate_steps.append({
            "step": "Query Count Mismatch",
            "content": f"Requested: {num_queries}, Generated: {len(synthetic_queries)}"
        })
        return {
            "intermediate_steps": intermediate_steps,
            "error": "# The number of generated queries does not match the requested number."
        }

    # Step 2: Process each synthetic query using choose_or_create_function
    for idx, query in enumerate(synthetic_queries, start=1):
        intermediate_steps.append({"step": f"Processing Query {idx}", "content": query})
        try:
            # Assuming choose_or_create_function is accessible within the scope
            # If it's in a different module, you might need to import it accordingly
            query_result = choose_or_create_function(query)
            results.append({
                "query": query,
                "result": query_result.get("execution_result"),
                "intermediate_steps": query_result.get("intermediate_steps", [])
            })
            intermediate_steps.append({
                "step": f"Executed Query {idx}",
                "content": query_result.get("execution_result")
            })
        except Exception as e:
            print(f"[ERROR] Processing query {idx} failed: {e}")
            intermediate_steps.append({
                "step": f"Error Processing Query {idx}",
                "content": str(e)
            })
            results.append({
                "query": query,
                "error": f"# Error processing query: {e}"
            })

    return {
        "intermediate_steps": intermediate_steps,
        "results": results
    }
