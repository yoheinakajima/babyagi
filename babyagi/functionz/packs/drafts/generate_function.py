
from functionz.core.framework import func

# Function 1: Fetch existing functions
@func.register_function(
    metadata={"description": "Fetch existing functions using display_functions_wrapper."},
    dependencies=["display_functions_wrapper"],
    imports=[
        {"name": "json", "lib": "json"}
    ]
)
def fetch_existing_functions(description: str) -> dict:
    """
    Fetches existing functions and returns them along with the initial intermediate_steps.

    Args:
        description (str): User description of the function to generate.

    Returns:
        dict: A dictionary containing existing functions and intermediate steps.
    """
    intermediate_steps = []
    try:
        existing_functions = display_functions_wrapper()
        print(f"[DEBUG] Existing Functions: {existing_functions}")
        intermediate_steps.append({"step": "Fetch Existing Functions", "content": existing_functions})
        return {"existing_functions": existing_functions, "intermediate_steps": intermediate_steps}
    except Exception as e:
        print(f"[ERROR] Failed to fetch existing functions: {e}")
        intermediate_steps.append({"step": "Error Fetching Existing Functions", "content": str(e)})
        return {"intermediate_steps": intermediate_steps, "error": "# Error fetching existing functions."}

# Function 2: Analyze internal functions
@func.register_function(
    metadata={"description": "Analyze internal functions and identify reusable and reference functions."},
    dependencies=["litellm", "FunctionSuggestion"],
    imports=[
        {"name": "litellm", "lib": "litellm"},
        {"name": "pydantic", "lib": "pydantic"},
        {"name": "typing", "lib": "typing"},
        {"name": "json", "lib": "json"},
    ]
)
def analyze_internal_functions(description: str, existing_functions: str, intermediate_steps: list) -> dict:
    """
    Analyzes existing functions to identify reusable and reference functions.

    Args:
        description (str): User description of the function to generate.
        existing_functions (str): Existing functions obtained from the previous step.
        intermediate_steps (list): List of intermediate steps.

    Returns:
        dict: A dictionary containing updated intermediate steps, reusable_functions, and reference_functions.
    """
    from litellm import completion
    from pydantic import BaseModel, Field, ValidationError
    from typing import List
    import json

    # Define Pydantic model for parsing internal function responses
    class FunctionSuggestion(BaseModel):
        reusable_functions: List[str] = Field(default_factory=list)
        reference_functions: List[str] = Field(default_factory=list)

    # System prompt for code generation adhering to the functionz framework guidelines.
    system_prompt = """
    You are an AI designed to help developers write Python functions using the functionz framework. Every function you generate must adhere to the following rules:

    Function Registration: All functions must be registered with the functionz framework using the @babyagi.register_function() decorator. Each function can include metadata, dependencies, imports, and key dependencies.

    Basic Function Registration Example:

    def function_name(param1, param2):
        # function logic here
        return result

    Metadata and Dependencies: When writing functions, you may include optional metadata (such as descriptions) and dependencies. Dependencies can be other functions or secrets (API keys, etc.).

    Import Handling: Manage imports by specifying them in the decorator as dictionaries with 'name' and 'lib' keys. Include these imports within the function body.

    Secret Management: When using API keys or authentication secrets, reference the stored key with globals()['key_name'].

    Error Handling: Functions should handle errors gracefully, catching exceptions if necessary.

    General Guidelines: Use simple, clean, and readable code. Follow the structure and syntax of the functionz framework. Ensure proper function documentation via metadata.
    """

    display_prompt = f"""You are an assistant helping a developer build a function using the functionz framework.

    The user has provided the following function description: {description}

    The current available functions are listed below. Please specify if any of these functions can be used directly (for reuse), or if any should be referenced while building the new function. Return your response as structured JSON.

    Available Functions:
    {existing_functions}
    """

    # Step 2.1: Make the LLM call using JSON mode with Pydantic model
    try:
        display_response = completion(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": display_prompt}
            ],
            response_format=FunctionSuggestion
        )
        print(f"[DEBUG] Display Response: {display_response}")
    except Exception as e:
        print(f"[ERROR] LLM call for FunctionSuggestion failed: {e}")
        intermediate_steps.append({"step": "Error in FunctionSuggestion LLM Call", "content": str(e)})
        return {"intermediate_steps": intermediate_steps, "error": "# Error during FunctionSuggestion analysis."}

    # Step 2.2: Access and parse the response
    try:
        content = display_response.choices[0].message.content
        print(f"[DEBUG] Raw Display Content: {content}")
        display_response_parsed = FunctionSuggestion.parse_raw(content)
        print(f"[DEBUG] Parsed FunctionSuggestion: {display_response_parsed}")
        intermediate_steps.append({"step": "Analyze Internal Functions", "content": display_response_parsed.dict()})
    except (ValidationError, IndexError, AttributeError, json.JSONDecodeError) as e:
        print(f"[ERROR] Parsing FunctionSuggestion response failed: {e}")
        intermediate_steps.append({"step": "Error Parsing FunctionSuggestion Response", "content": str(e)})
        return {"intermediate_steps": intermediate_steps, "error": "# Error parsing FunctionSuggestion response."}

    reusable_functions = display_response_parsed.reusable_functions
    reference_functions = display_response_parsed.reference_functions
    print(f"[DEBUG] Reusable Functions: {reusable_functions}")
    print(f"[DEBUG] Reference Functions: {reference_functions}")

    return {
        "intermediate_steps": intermediate_steps,
        "reusable_functions": reusable_functions,
        "reference_functions": reference_functions
    }

# Function 3: Fetch function codes
@func.register_function(
    metadata={"description": "Fetch function codes for given function names using get_function_wrapper."},
    dependencies=["get_function_wrapper"],
    imports=[
        {"name": "json", "lib": "json"},
        {"name": "typing", "lib": "typing"},
    ]
)
def fetch_function_codes(function_names, intermediate_steps):
    """
    Fetches function codes for given function names.

    Args:
        function_names (List[str]): List of function names to fetch.
        intermediate_steps (list): List of intermediate steps.

    Returns:
        dict: A dictionary containing updated intermediate steps and function_codes.
    """
    from typing import List
    try:
        function_codes = {
            func_name: get_function_wrapper(func_name).get("code", "")
            for func_name in function_names
        }
        print(f"[DEBUG] Function Codes: {function_codes}")
        intermediate_steps.append({"step": "Fetch Function Codes", "content": function_codes})
        return {
            "intermediate_steps": intermediate_steps,
            "function_codes": function_codes
        }
    except Exception as e:
        print(f"[ERROR] Fetching function codes failed: {e}")
        intermediate_steps.append({"step": "Error Fetching Function Codes", "content": str(e)})
        return {"intermediate_steps": intermediate_steps, "error": "# Error fetching function codes."}

# Function 4: Determine required external APIs
@func.register_function(
    metadata={"description": "Determine required external APIs based on the user's function description."},
    dependencies=["litellm"],
    imports=[
        {"name": "litellm", "lib": "litellm"},
        {"name": "pydantic", "lib": "pydantic"},
        {"name": "typing", "lib": "typing"},
        {"name": "json", "lib": "json"},
    ]
)
def determine_required_external_apis(description: str, intermediate_steps: list) -> dict:
    """
    Determines required external APIs based on the user's function description.

    Args:
        description (str): User description of the function to generate.
        intermediate_steps (list): List of intermediate steps.

    Returns:
        dict: A dictionary containing updated intermediate steps and external_apis as a list of dictionaries.
    """
    from litellm import completion
    from pydantic import BaseModel, Field, ValidationError, validator
    from typing import List, Optional, Union
    import json

    # Define Pydantic models
    class Endpoint(BaseModel):
        method: Optional[str]
        url: str
        description: Optional[str] = None

    class APIDetails(BaseModel):
        api_name: str = Field(alias="name")  # Use alias to map 'name' to 'api_name'
        purpose: str
        endpoints: Optional[List[Union[Endpoint, str]]] = Field(default_factory=list)

        @validator("endpoints", pre=True, each_item=True)
        def convert_to_endpoint(cls, v):
            """Convert string URLs into Endpoint objects if necessary."""
            if isinstance(v, str):
                return Endpoint(url=v)  # Create an Endpoint object from a URL string
            return v

    class APIResponse(BaseModel):
        name: str
        purpose: str
        endpoints: List[Endpoint]

    # System prompt
    system_prompt = """
    [Your existing system prompt here]
    """

    prompt_for_apis = f"""You are an assistant analyzing function requirements.

    The user has provided the following function description: {description}.

    Identify if this function will require external APIs (including SDKs or libraries). If so, return a structured JSON with a list of external APIs, their purposes, and any relevant endpoints."""

    try:
        api_response = completion(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_for_apis}
            ],
            response_format=APIDetails
        )
        print(f"[DEBUG] API Response: {api_response}")
    except Exception as e:
        print(f"[ERROR] LLM call for APIResponse failed: {e}")
        intermediate_steps.append({"step": "Error in APIResponse LLM Call", "content": str(e)})
        return {"intermediate_steps": intermediate_steps, "error": "# Error during APIResponse analysis."}

    # Step 3.2: Access and parse the API response
    try:
        content = api_response.choices[0].message.content
        print(f"[DEBUG] Raw API Content: {content}")
        api_response_parsed = APIResponse.parse_raw(content)
        print(f"[DEBUG] Parsed APIResponse: {api_response_parsed}")
        intermediate_steps.append({"step": "Identify External API", "content": api_response_parsed.dict()})

        # Ensure external_apis is always a list
        external_apis = [api_response_parsed.dict()]  # Wrap in a list
    except (ValidationError, IndexError, AttributeError, json.JSONDecodeError) as e:
        print(f"[ERROR] Parsing APIResponse failed: {e}")
        intermediate_steps.append({"step": "Error Parsing APIResponse", "content": str(e)})
        return {"intermediate_steps": intermediate_steps, "error": "# Error parsing APIResponse."}

    return {
        "intermediate_steps": intermediate_steps,
        "external_apis": external_apis  # Now a list of dicts
    }



# Function 5: Handle API documentation and extraction
@func.register_function(
    metadata={"description": "Search API documentation and extract relevant information."},
    dependencies=["serpapi_search_v2", "scrape_website", "litellm"],
    key_dependencies=["serpapi_api_key", "firecrawl_api_key"],
    imports=[
        {"name": "litellm", "lib": "litellm"},
        {"name": "pydantic", "lib": "pydantic"},
        {"name": "typing", "lib": "typing"},
        {"name": "json", "lib": "json"},
        {"name": "urllib", "lib": "urllib"},
    ]
)
def handle_api_documentation(api_name: str, description: str, intermediate_steps: list) -> dict:
    """
    Searches API documentation for a given API and extracts relevant information.

    Args:
        api_name (str): Name of the API to search for.
        description (str): User description of the function to generate.
        intermediate_steps (list): List of intermediate steps.

    Returns:
        dict: A dictionary containing updated intermediate steps and api_contexts.
    """
    from litellm import completion
    from pydantic import BaseModel, Field, ValidationError
    from typing import List
    import json
    from urllib.parse import urlparse

    # Define Pydantic models
    class URLSelection(BaseModel):
        selected_urls: List[str] = Field(default_factory=list)

    # Updated ExtractionInfo model with 'requires_more_info'
    class ExtractionInfo(BaseModel):
        relevant_info: str
        additional_urls: List[str] = Field(default_factory=list)
        requires_more_info: bool

    # System prompt
    system_prompt = """
    You are an AI designed to help developers write Python functions using the functionz framework. Every function you generate must adhere to the following rules:

    Function Registration: All functions must be registered with the functionz framework using the @babyagi.register_function() decorator. Each function can include metadata, dependencies, imports, and key dependencies.

    Basic Function Registration Example:

    def function_name(param1, param2):
        # function logic here
        return result

    Metadata and Dependencies: When writing functions, you may include optional metadata (such as descriptions) and dependencies. Dependencies can be other functions or secrets (API keys, etc.).

    Import Handling: Manage imports by specifying them in the decorator as dictionaries with 'name' and 'lib' keys. Include these imports within the function body.

    Secret Management: When using API keys or authentication secrets, reference the stored key with globals()['key_name'].

    Error Handling: Functions should handle errors gracefully, catching exceptions if necessary.

    General Guidelines: Use simple, clean, and readable code. Follow the structure and syntax of the functionz framework. Ensure proper function documentation via metadata.
    """

    # Function to check if a URL is valid
    def is_valid_url(url: str) -> bool:
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    # Function to chunk text
    def chunk_text(text: str, chunk_size: int = 100000, overlap: int = 10000) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            if end < len(text):
                # Find the last newline within the overlap
                last_newline = text.rfind('\n', end - overlap, end)
                if last_newline != -1:
                    end = last_newline + 1
            chunks.append(text[start:end])
            start = end - overlap
        return chunks

    search_query = f"{api_name} API documentation python"
    print(f"[DEBUG] Searching for API documentation with query: {search_query}")
    try:
        search_results = serpapi_search_v2(query=search_query)
        print(f"[DEBUG] Search Results for {api_name}: {search_results}")
        intermediate_steps.append({"step": f"Search API Documentation for {api_name}", "content": search_results})
    except Exception as e:
        print(f"[ERROR] serpapi_search_v2 failed for {api_name}: {e}")
        intermediate_steps.append({"step": f"Error Searching API Documentation for {api_name}", "content": str(e)})
        return {"intermediate_steps": intermediate_steps, "error": "# Error searching API documentation."}

    link_selection_prompt = f"""You are given the following search results for the query "{search_query}":
    {json.dumps(search_results)}

    Which links seem most relevant for obtaining Python API documentation? Return them as a structured JSON list of URLs."""

    try:
        link_selection_response = completion(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": link_selection_prompt}
            ],
            response_format=URLSelection
        )
        print(f"[DEBUG] Link Selection Response for {api_name}: {link_selection_response}")
    except Exception as e:
        print(f"[ERROR] LLM call for URLSelection failed for {api_name}: {e}")
        intermediate_steps.append({"step": f"Error in URLSelection LLM Call for {api_name}", "content": str(e)})
        return {"intermediate_steps": intermediate_steps, "error": "# Error in URLSelection LLM call."}

    # Step 4.2: Access and parse the link selection response
    try:
        content = link_selection_response.choices[0].message.content
        print(f"[DEBUG] Raw Link Selection Content for {api_name}: {content}")
        link_selection_parsed = URLSelection.parse_raw(content)
        print(f"[DEBUG] Parsed URLSelection for {api_name}: {link_selection_parsed}")
        intermediate_steps.append({"step": f"Select Relevant URLs for {api_name}", "content": link_selection_parsed.dict()})
    except (ValidationError, IndexError, AttributeError, json.JSONDecodeError) as e:
        print(f"[ERROR] Parsing URLSelection response for {api_name} failed: {e}")
        intermediate_steps.append({"step": f"Error Parsing URLSelection Response for {api_name}", "content": str(e)})
        return {"intermediate_steps": intermediate_steps, "error": "# Error parsing URLSelection response."}

    selected_urls = link_selection_parsed.selected_urls or []
    print(f"[DEBUG] Selected URLs for {api_name}: {selected_urls}")
    scraped_urls = set()
    api_scrape_info = {}
    api_contexts = []
    accumulated_info = ""  # To accumulate relevant info

    requires_more_info = True  # Initialize to True to start the loop

    # Step 5: Scrape and recursively explore additional URLs until no more info is needed
    while selected_urls and requires_more_info:
        current_url = selected_urls.pop(0)
        print(f"[DEBUG] Scraping URL: {current_url}")
        if current_url in scraped_urls or not is_valid_url(current_url):
            print(f"[DEBUG] URL already scraped or invalid: {current_url}")
            continue

        try:
            scrape_result = scrape_website(current_url)
            print(f"[DEBUG] Scrape Result for {current_url}: {scrape_result}")
        except Exception as e:
            print(f"[ERROR] scrape_website failed for {current_url}: {e}")
            intermediate_steps.append({"step": f"Error Scraping URL: {current_url}", "content": str(e)})
            continue  # Skip to the next URL

        scraped_urls.add(current_url)
        if not scrape_result.get("error"):
            api_scrape_info[current_url] = scrape_result
            intermediate_steps.append({"step": f"Scrape URL: {current_url}", "content": scrape_result})
        else:
            print(f"[WARN] Error in scrape_result for {current_url}: {scrape_result.get('error')}")
            intermediate_steps.append({"step": f"Scrape Error for URL: {current_url}", "content": scrape_result.get("error")})
            continue  # Skip to the next URL

        # Step 6: Use LLM to extract relevant info and decide if more info is needed
        extraction_prompt = f"""The user wants to create a function described as follows: {description}.
You have accumulated the following relevant API information so far:
{accumulated_info}

You have just scraped the following new API documentation:
{json.dumps(scrape_result)}

Based on the new information, extract any additional relevant API methods, endpoints, and usage patterns needed to implement the user's function. Indicate whether more information is required by setting 'requires_more_info' to true or false. If any other URLs should be scraped for further information, include them in the 'additional_urls' field."""

        # Chunk the extraction prompt if it's too long
        extraction_prompt_chunks = chunk_text(extraction_prompt)
        extraction_results = []

        for chunk in extraction_prompt_chunks:
            try:
                extraction_response = completion(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": chunk}
                    ],
                    response_format=ExtractionInfo
                )
                print(f"[DEBUG] Extraction Response: {extraction_response}")
                extraction_results.append(extraction_response)
            except Exception as e:
                print(f"[ERROR] LLM call for ExtractionInfo failed: {e}")
                intermediate_steps.append({"step": "Error in ExtractionInfo LLM Call", "content": str(e)})
                continue  # Skip to the next chunk

        # Combine extraction results
        combined_extraction = {
            "relevant_info": "",
            "additional_urls": [],
            "requires_more_info": False
        }
        for result in extraction_results:
            try:
                content = result.choices[0].message.content
                parsed_result = ExtractionInfo.parse_raw(content)
                combined_extraction["relevant_info"] += parsed_result.relevant_info + "\n"
                combined_extraction["additional_urls"].extend(parsed_result.additional_urls)
                if parsed_result.requires_more_info:
                    combined_extraction["requires_more_info"] = True
            except (ValidationError, IndexError, AttributeError, json.JSONDecodeError) as e:
                print(f"[ERROR] Parsing ExtractionInfo response failed: {e}")
                intermediate_steps.append({"step": "Error Parsing ExtractionInfo Response", "content": str(e)})

        # Update accumulated info
        accumulated_info += combined_extraction["relevant_info"]
        print(f"[DEBUG] Updated Accumulated Info: {accumulated_info}")

        # Include extracted info in API contexts
        api_contexts.append(combined_extraction["relevant_info"])
        print(f"[DEBUG] Updated API Contexts: {api_contexts}")

        # Queue additional URLs for scraping
        new_urls = [url for url in combined_extraction["additional_urls"] if url not in scraped_urls and is_valid_url(url)]
        print(f"[DEBUG] New URLs to Scrape: {new_urls}")
        selected_urls.extend(new_urls)

        # Check if more information is required
        requires_more_info = combined_extraction["requires_more_info"]
        print(f"[DEBUG] Requires More Info: {requires_more_info}")

    return {
        "intermediate_steps": intermediate_steps,
        "api_contexts": api_contexts
    }


# Function 6: Generate final function code
@func.register_function(
    metadata={"description": "Generate the final function code using all gathered information."},
    dependencies=["litellm"],
    imports=[
        {"name": "litellm", "lib": "litellm"},
        {"name": "json", "lib": "json"},
        {"name": "typing", "lib": "typing"},
    ]
)
def generate_final_function_code(description: str, reusable_function_code: dict, reference_function_code: dict, api_contexts: list, intermediate_steps: list) -> dict:
    """
    Generates the final function code using all gathered information.

    Args:
        description (str): User description of the function to generate.
        reusable_function_code (dict): Codes of reusable functions.
        reference_function_code (dict): Codes of reference functions.
        api_contexts (list): List of API contexts.
        intermediate_steps (list): List of intermediate steps.

    Returns:
        dict: A dictionary containing updated intermediate steps and the combined final function details.
    """
    from litellm import completion
    from pydantic import BaseModel, Field, ValidationError
    from typing import Dict, Any, List, Optional
    import json

    # Define Pydantic model
    class GeneratedFunction(BaseModel):
        name: str
        code: str
        metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
        imports: Optional[List[Dict[str, str]]] = Field(default_factory=list)
        dependencies: List[str] = Field(default_factory=list)
        key_dependencies: List[str] = Field(default_factory=list)
        triggers: List[str] = Field(default_factory=list)

        class Config:
            extra = "forbid"

    # System prompt
    system_prompt = """
    You are an AI designed to help developers write Python functions using the functionz framework. Every function you generate must adhere to the following rules:

    Function Registration: All functions must be registered with the functionz framework using the @babyagi.register_function() decorator. Each function can include metadata, dependencies, imports, and key dependencies.

    Basic Function Registration Example:

    def function_name(param1, param2):
        # function logic here
        return result

    Metadata and Dependencies: When writing functions, you may include optional metadata (such as descriptions) and dependencies. Dependencies can be other functions or secrets (API keys, etc.).

    Import Handling: Manage imports by specifying them in the decorator as dictionaries with 'name' and 'lib' keys. Include these imports within the function body.

    Secret Management: When using API keys or authentication secrets, reference the stored key with globals()['key_name'].

    Error Handling: Functions should handle errors gracefully, catching exceptions if necessary.

    General Guidelines: Use simple, clean, and readable code. Follow the structure and syntax of the functionz framework. Ensure proper function documentation via metadata.
    """

    # Function to chunk text
    def chunk_text(text: str, chunk_size: int = 100000, overlap: int = 10000) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            if end < len(text):
                # Find the last newline within the overlap
                last_newline = text.rfind('\n', end - overlap, end)
                if last_newline != -1:
                    end = last_newline + 1
            chunks.append(text[start:end])
            start = end - overlap
        return chunks

    final_prompt = f"""{system_prompt}

    The user wants to create a function with the following description: {description}.

    You have the following internal reusable functions:
    {json.dumps(reusable_function_code)}

    You have the following internal reference functions:
    {json.dumps(reference_function_code)}

    You have the following context on the necessary external APIs and their usage:
    {json.dumps(api_contexts)}

    Generate a complete function using the functionz framework that adheres to the provided guidelines and utilizes the specified internal and external functions. Ensure the function is registered with the correct metadata, dependencies, and includes all relevant imports.

    Provide the function details in a structured format including:
    1. Function name
    2. Complete function code (do not the @babyagi.register_function decorator)
    3. Metadata (description)
    4. Imports
    5. Dependencies
    6. Key dependencies
    7. Triggers (if any)
    """

    # Chunk the final prompt if it's too long
    final_prompt_chunks = chunk_text(final_prompt)
    final_results = []

    for chunk in final_prompt_chunks:
        try:
            final_response = completion(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": chunk}
                ],
                response_format=GeneratedFunction
            )
            print(f"[DEBUG] Final Response: {final_response}")
            final_results.append(final_response)
        except Exception as e:
            print(f"[ERROR] LLM call for GeneratedFunction failed: {e}")
            intermediate_steps.append({"step": "Error in GeneratedFunction LLM Call", "content": str(e)})
            return {"intermediate_steps": intermediate_steps, "error": "# Error during GeneratedFunction generation."}

    # Combine final results
    combined_final = {
        "name": "",
        "code": "",
        "metadata": {},
        "imports": [],
        "dependencies": [],
        "key_dependencies": [],
        "triggers": []
    }
    for result in final_results:
        try:
            content = result.choices[0].message.content
            parsed_result = GeneratedFunction.parse_raw(content)
            if not combined_final["name"]:
                combined_final["name"] = parsed_result.name
            combined_final["code"] += parsed_result.code + "\n"
            if parsed_result.metadata:
                combined_final["metadata"].update(parsed_result.metadata or {})
            if parsed_result.imports:
                combined_final["imports"].extend(parsed_result.imports)
            if parsed_result.dependencies:
                combined_final["dependencies"].extend(parsed_result.dependencies)
            if parsed_result.key_dependencies:
                combined_final["key_dependencies"].extend(parsed_result.key_dependencies)
            if parsed_result.triggers:
                combined_final["triggers"].extend(parsed_result.triggers)

        except (ValidationError, IndexError, AttributeError, json.JSONDecodeError) as e:
            print(f"[ERROR] Parsing GeneratedFunction response failed: {e}")
            intermediate_steps.append({"step": "Error Parsing GeneratedFunction Response", "content": str(e)})
            return {"intermediate_steps": intermediate_steps, "error": "# Error parsing GeneratedFunction response."}

    # Remove duplicates from lists
    combined_final["imports"] = list({json.dumps(imp): imp for imp in combined_final["imports"]}.values())
    combined_final["dependencies"] = list(set(combined_final["dependencies"]))
    combined_final["key_dependencies"] = list(set(combined_final["key_dependencies"]))
    combined_final["triggers"] = list(set(combined_final["triggers"]))

    print(f"[DEBUG] Combined Final GeneratedFunction: {combined_final}")
    intermediate_steps.append({"step": "Generate Final Function", "content": combined_final})

    return {
        "intermediate_steps": intermediate_steps,
        "combined_final": combined_final
    }

# Function 7: Add function to database
@func.register_function(
    metadata={"description": "Add the generated function to the database."},
    dependencies=["add_new_function"],
    imports=[
        {"name": "json", "lib": "json"},
    ]
)
def add_function_to_database(combined_final: dict, intermediate_steps: list) -> dict:
    """
    Adds the generated function to the database.

    Args:
        combined_final (dict): The combined final function details.
        intermediate_steps (list): List of intermediate steps.

    Returns:
        dict: A dictionary containing updated intermediate steps and the success status.
    """
    try:
        success = add_new_function(
            name=combined_final["name"],
            code=combined_final["code"],
            metadata=combined_final["metadata"],
            imports=combined_final["imports"],
            dependencies=combined_final["dependencies"],
            key_dependencies=combined_final["key_dependencies"],
            triggers=combined_final["triggers"]
        )
        intermediate_steps.append({"step": "Add Function to Database", "content": {"success": success}})
    except Exception as e:
        print(f"[ERROR] Failed to add function to database: {e}")
        intermediate_steps.append({"step": "Error Adding Function to Database", "content": str(e)})
        success = False

    return {
        "intermediate_steps": intermediate_steps,
        "success": success
    }

# Main Function: Orchestrate all steps
@func.register_function(
    metadata={"description": "Main function to generate a function from a description."},
    dependencies=[
        "fetch_existing_functions",
        "analyze_internal_functions",
        "fetch_function_codes",
        "determine_required_external_apis",
        "handle_api_documentation",
        "generate_final_function_code",
        "add_function_to_database"
    ],
    imports=[
        {"name": "json", "lib": "json"},
        {"name": "typing", "lib": "typing"},
    ]
)
def generate_function_from_description(description: str) -> dict:
    """
    Main function that generates a Python function based on a user-provided description.

    Args:
        description (str): User description of the function to generate.

    Returns:
        dict: A dictionary containing intermediate steps, the final generated function code, and whether it was successfully added to the database.
    """
    intermediate_steps = []

    # Step 1: Fetch existing functions
    result = fetch_existing_functions(description)
    if "error" in result:
        return {"intermediate_steps": result["intermediate_steps"], "final_code": result["error"], "added_to_database": False}
    existing_functions = result["existing_functions"]
    intermediate_steps.extend(result["intermediate_steps"])

    # Step 2: Analyze internal functions
    result = analyze_internal_functions(description, existing_functions, intermediate_steps)
    if "error" in result:
        return {"intermediate_steps": result["intermediate_steps"], "final_code": result["error"], "added_to_database": False}
    intermediate_steps = result["intermediate_steps"]
    reusable_functions = result["reusable_functions"]
    reference_functions = result["reference_functions"]

    # Step 3: Fetch function codes for reusable and reference functions
    reusable_function_code = {}
    if reusable_functions:
        result = fetch_function_codes(reusable_functions, intermediate_steps)
        if "error" in result:
            return {"intermediate_steps": result["intermediate_steps"], "final_code": result["error"], "added_to_database": False}
        intermediate_steps = result["intermediate_steps"]
        reusable_function_code = result["function_codes"]

    reference_function_code = {}
    if reference_functions:
        result = fetch_function_codes(reference_functions, intermediate_steps)
        if "error" in result:
            return {"intermediate_steps": result["intermediate_steps"], "final_code": result["error"], "added_to_database": False}
        intermediate_steps = result["intermediate_steps"]
        reference_function_code = result["function_codes"]

    # Step 4: Determine required external APIs
    result = determine_required_external_apis(description, intermediate_steps)
    if "error" in result:
        return {"intermediate_steps": result["intermediate_steps"], "final_code": result["error"], "added_to_database": False}
    intermediate_steps = result["intermediate_steps"]
    external_apis_dicts = result["external_apis"]

    # Ensure external_apis_dicts is a list
    if not isinstance(external_apis_dicts, list):
        external_apis_dicts = [external_apis_dicts]

    # Reconstruct APIResponse objects from dicts
    from typing import Optional, List
    from pydantic import BaseModel

    class Endpoint(BaseModel):
        method: Optional[str]
        url: str
        description: Optional[str] = None

    class APIResponse(BaseModel):
        name: str
        purpose: str
        endpoints: List[Endpoint]

    external_apis = []
    for api_dict in external_apis_dicts:
        api_response_parsed = APIResponse(**api_dict)
        external_apis.append(api_response_parsed)

    # Step 5: Handle API documentation and extract contexts
    api_contexts = []
    for api_response_parsed in external_apis:
        api_name = api_response_parsed.name
        result = handle_api_documentation(api_name, description, intermediate_steps)
        if "error" in result:
            return {"intermediate_steps": result["intermediate_steps"], "final_code": result["error"], "added_to_database": False}
        intermediate_steps = result["intermediate_steps"]
        api_contexts.extend(result["api_contexts"])

    # Step 6: Generate final function code
    result = generate_final_function_code(description, reusable_function_code, reference_function_code, api_contexts, intermediate_steps)
    if "error" in result:
        return {"intermediate_steps": result["intermediate_steps"], "final_code": result["error"], "added_to_database": False}
    intermediate_steps = result["intermediate_steps"]
    combined_final = result["combined_final"]

    # Step 7: Add function to database
    result = add_function_to_database(combined_final, intermediate_steps)
    intermediate_steps = result["intermediate_steps"]
    success = result["success"]

    return {
        "intermediate_steps": intermediate_steps,
        "final_code": combined_final["code"],
        "added_to_database": success
    }
