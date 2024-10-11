# packs/ai_generator.py

from functionz.core.framework import func

@func.register_function(
    metadata={"description": "GPT Call function using LiteLLm"},
    imports=["litellm"],
    key_dependencies=["openai_api_key"]
)
def gpt_call(prompt: str) -> str:
    from litellm import completion
    messages = [{"role": "user", "content": prompt}]
    response = completion(model="gpt-4o", messages=messages)
    return response['choices'][0]['message']['content']

@func.register_function(
    metadata={"description": "Generates a description for a function using LiteLLm"},
    dependencies=["gpt_call"]
)
def description_writer(function_code: str) -> str:
    prompt = (
        f"Provide a concise and clear description for the following Python function:\n\n"
        f"{function_code}\n\n"
        f"Description:"
    )
    description = func.gpt_call(prompt)
    return description

@func.register_function(
    metadata={"description": "Generates and updates descriptions for functions lacking one or having an empty description"},
    dependencies=["description_writer"],
    triggers=["function_added_or_updated"]
)
def ai_description_generator(function_name: str) -> None:
    print(f"Generating AI description for function: {function_name}")
    function = func.db.get_function(function_name)
    if not function:
        print(f"Function '{function_name}' not found in the database.")
        return

    description = function.get('metadata', {}).get('description', '').strip()
    function_code = function.get('code', '')

    if not description and function_code.strip():
        #print(f"Generating description for function '{function_name}'.")
        generated_description = func.description_writer(function_code)
        func.update_function(
            name=function_name,
            metadata={"description": generated_description}
        )
        print(f"Description for function '{function_name}' has been generated and updated.")
        return f"Description for function '{function_name}' has been generated and updated."
    elif not function_code.strip():
        print(f"Function '{function_name}' has no code to generate a description.")
        return f"Function '{function_name}' has no code to generate a description."
    else:
        print(f"Function '{function_name}' already has a non-empty description.")
        return f"Function '{function_name}' already has a non-empty description."

@func.register_function(
    metadata={"description": "Scans all functions and generates descriptions for those lacking one"},
    dependencies=["ai_description_generator"]
)
def generate_missing_descriptions() -> None:
    all_functions = func.db.get_all_functions()
    missing_description_functions = [
        func_info['name'] for func_info in all_functions
        if not func_info.get('metadata', {}).get('description')
    ]
    if not missing_description_functions:
        print("All functions already have descriptions.")
        return
    print(f"Found {len(missing_description_functions)} function(s) without descriptions. Generating descriptions...")
    for function_name in missing_description_functions:
        func.ai_description_generator(function_name)
    print("Description generation process completed.")


@func.register_function(
    metadata={"description": "Embeds an input using LiteLLM"},
    imports=["litellm"],
    key_dependencies=["openai_api_key"]
)
def embed_input(input_text: str, model: str = "text-embedding-ada-002", 
                encoding_format: str = "float", dimensions: int = None, 
                timeout: int = 600) -> list:
    from litellm import embedding
    import os

    # Set OpenAI API Key from environment variables
    os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')

    # Prepare the embedding request with optional parameters
    embedding_params = {
        "model": model,
        "input": [input_text],
        "encoding_format": encoding_format,
        "timeout": timeout
    }

    if dimensions:
        embedding_params["dimensions"] = dimensions

    # Call the LiteLLM embedding function
    response = embedding(**embedding_params)

    # Return the embedding from the response
    return response['data'][0]['embedding']


@func.register_function(
    metadata={"description": "Embeds and updates a function's description if it exists"},
    dependencies=["embed_input"],
    imports=["os","csv"]
)
def embed_function_description(function: str) -> None:
    print(f"Embedding description for function: {function}")
    # Retrieve the function details from the database
    function_data = func.db.get_function(function)
    if not function_data:
        print(f"Function '{function}' not found in the database.")
        return

    description = function_data.get('metadata', {}).get('description', '').strip()
    if description:
        print(f"Embedding description for function '{function}'.")
        embedding = func.embed_input(description)

        # Check if 'function_embeddings.csv' exists, create it if not
        file_path = 'function_embeddings.csv'
        file_exists = os.path.isfile(file_path)

        # Create a list to store CSV data
        rows = []

        if file_exists:
            with open(file_path, mode='r') as file:
                reader = csv.reader(file)
                rows = list(reader)

        # Look for the function in the existing rows
        function_found = False
        for i, row in enumerate(rows):
            if row[0] == function:  # function column is the first column
                rows[i][1] = str(embedding)  # Update the embedding
                function_found = True
                print(f"Updated embedding for function '{function}'.")

        if not function_found:
            # Add a new row if the function is not found
            rows.append([function, str(embedding)])
            print(f"Added new function '{function}' with its embedding.")

        # Write back the data to the CSV file (create or update)
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows)

        print(f"Embedding for function '{function}' has been saved.")
        return embedding
    else:
        print(f"Function '{function}' has no description to embed.")
        return f"Function '{function}' has no description to embed."



@func.register_function(
    metadata={"description": "Finds similar functions based on the provided description"},
    dependencies=["embed_input"],
    imports=["numpy", "csv", "sklearn","os"]
)
def find_similar_function(description: str, top_n: int = 3):
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    # Step 1: Embed the input description
    #print(f"Embedding input description: {description}")
    input_embedding = func.embed_input(description)

    # Step 2: Load stored embeddings and descriptions from CSV
    file_path = 'function_embeddings.csv'
    stored_embeddings = []
    stored_functions = []

    if not os.path.isfile(file_path):
        print(f"No embeddings found in {file_path}.")
        return []

    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            stored_functions.append(row[0])
            stored_embeddings.append(np.fromstring(row[1].strip("[]"), sep=','))

    if not stored_embeddings:
        print("No embeddings stored.")
        return []

    # Step 3: Calculate cosine similarity between the input embedding and stored embeddings
    similarities = cosine_similarity([input_embedding], stored_embeddings)

    # Step 4: Sort stored functions by similarity
    sorted_indices = np.argsort(similarities[0])[::-1]  # Sort in descending order

    # Step 5: Return the top N most similar functions
    similar_functions = [stored_functions[i] for i in sorted_indices[:top_n]]

    print(f"Top {top_n} similar functions: {similar_functions}")
    return similar_functions


@func.register_function(
    metadata={"description": "Generates embeddings for functions missing from the CSV"},
    dependencies=["embed_function_description"],
    imports=["os", "csv"]
)
def generate_missing_embeddings() -> None:
    # Step 1: Retrieve all functions from the database
    all_functions = func.db.get_all_functions()
    all_function_names = [func_info['name'] for func_info in all_functions]

    # Step 2: Check if 'function_embeddings.csv' exists
    file_path = 'function_embeddings.csv'
    file_exists = os.path.isfile(file_path)

    # Read existing embeddings from CSV if the file exists
    embedded_functions = []
    if file_exists:
        with open(file_path, mode='r') as file:
            reader = csv.reader(file)
            embedded_functions = [row[0] for row in reader]  # First column is the function name

    # Step 3: Find functions without embeddings
    missing_embeddings = [func_name for func_name in all_function_names if func_name not in embedded_functions]

    if not missing_embeddings:
        print("All functions already have embeddings.")
        return

    print(f"Found {len(missing_embeddings)} function(s) without embeddings. Generating embeddings...")

    # Step 4: Embed the functions that are missing
    for function_name in missing_embeddings:
        print(f"Embedding function: {function_name}")
        func.embed_function_description(function_name)

    print("Embedding generation process completed.")



@func.register_function(
    metadata={"description": "Chooses a function to use"},
    dependencies=["get_all_functions","gpt_call"]
)
def choose_function(prompt: str) -> str:
    functions = func.get_all_functions()
    prompt = (
        f"Which functions are most relevant to the following input? It could be ones to use or look at as reference to build a new one:\n\n"
        f"{prompt}\n\n"
        f"Functions:{functions}"
    )
    choice = func.gpt_call(prompt)
    return {"functions":functions,"choice":choice}