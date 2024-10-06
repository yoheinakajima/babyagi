from functionz.core.framework import func

@func.register_function(
    metadata={"description": "Analyze a user-provided function description, identify required APIs or internal functions, and generate a complete function using the functionz framework."},
    dependencies=["serpapi_search_v2", "scrape_website", "display_functions_wrapper", "get_function_wrapper", "add_new_function"],
    key_dependencies=["openai_api_key", "serpapi_api_key", "firecrawl_api_key"],
    imports=[
        {"name": "json", "lib": "json"},
        {"name": "litellm", "lib": "litellm"},
        {"name": "pydantic", "lib": "pydantic"},
        {"name": "typing", "lib": "typing"},
        {"name": "os", "lib": "os"},
        {"name": "urllib", "lib": "urllib"}
    ]
)
def generate_function_from_description(description: str) -> dict:
    """
    Generates a Python function based on a user-provided description using the functionz framework. It analyzes internal functions, identifies required APIs, searches for API documentation, scrapes relevant information, synthesizes a complete function, and adds it to the database.

    Args:
        description (str): User description of the function to generate.

    Returns:
        dict: A dictionary containing intermediate steps, the final generated function code, and whether it was successfully added to the database.
    """

    from litellm import completion
    from pydantic import BaseModel, Field, ValidationError, validator
    from typing import List, Optional, Dict, Any, Union
    from urllib.parse import urlparse
    import json

    # System prompt for code generation adhering to the functionz framework guidelines.
    system_prompt = """
    You are an AI designed to help developers write Python functions using the functionz framework. Every function you generate must adhere to the following rules:

    Function Registration: All functions must be registered with the functionz framework using the @babyagi.register_function() decorator. Each function can include metadata, dependencies, imports, and key dependencies.

    Basic Function Registration Example:

    @babyagi.register_function()
    def function_name(param1, param2):
        # function logic here
        return result

    Metadata and Dependencies: When writing functions, you may include optional metadata (such as descriptions) and dependencies. Dependencies can be other functions or secrets (API keys, etc.).

    Import Handling: Manage imports by specifying them in the decorator as dictionaries with 'name' and 'lib' keys. Include these imports within the function body.

    Secret Management: When using API keys or authentication secrets, reference the stored key with globals()['key_name'].

    Error Handling: Functions should handle errors gracefully, catching exceptions if necessary.

    General Guidelines: Use simple, clean, and readable code. Follow the structure and syntax of the functionz framework. Ensure proper function documentation via metadata.
    """

    intermediate_steps = []

    # Define Pydantic models for parsing internal function responses
    class FunctionSuggestion(BaseModel):
        reusable_functions: List[str] = Field(default_factory=list)
        reference_functions: List[str] = Field(default_factory=list)

    # Define a new model for the endpoint structure
    class Endpoint(BaseModel):
        method: Optional[str]
        url: str
        description: Optional[str] = None

    # Update the APIDetails model to match the response structure
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

    class URLSelection(BaseModel):
        selected_urls: List[str] = Field(default_factory=list)

    class ExtractionInfo(BaseModel):
        relevant_info: str
        additional_urls: List[str] = Field(default_factory=list)

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

    def is_valid_url(url: str) -> bool:
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

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

    # Step 1: Check for existing internal functions using display_functions_wrapper
    try:
        existing_functions = display_functions_wrapper()
        print(f"[DEBUG] Existing Functions: {existing_functions}")
        intermediate_steps.append({"step": "Fetch Existing Functions", "content": existing_functions})
    except Exception as e:
        print(f"[ERROR] Failed to fetch existing functions: {e}")
        intermediate_steps.append({"step": "Error Fetching Existing Functions", "content": str(e)})
        return {"intermediate_steps": intermediate_steps, "final_code": "# Error fetching existing functions.", "added_to_database": False}

    # Step 2: Use an LLM to analyze which internal functions are useful
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
        return {"intermediate_steps": intermediate_steps, "final_code": "# Error during FunctionSuggestion analysis.", "added_to_database": False}

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
        return {"intermediate_steps": intermediate_steps, "final_code": "# Error parsing FunctionSuggestion response.", "added_to_database": False}


    # Parse reusable and reference function lists
    reusable_functions = display_response_parsed.reusable_functions
    reference_functions = display_response_parsed.reference_functions
    print(f"[DEBUG] Reusable Functions: {reusable_functions}")
    print(f"[DEBUG] Reference Functions: {reference_functions}")

    # Check if reusable or reference functions are empty before calling `get_function_wrapper`
    reusable_function_code = {}
    if reusable_functions:
        try:
            reusable_function_code = {
                func_name: get_function_wrapper(func_name).get("code", "")
                for func_name in reusable_functions
            }
            print(f"[DEBUG] Reusable Function Codes: {reusable_function_code}")
            intermediate_steps.append({"step": "Fetch Reusable Function Codes", "content": reusable_function_code})
        except Exception as e:
            print(f"[ERROR] Fetching reusable function codes failed: {e}")
            intermediate_steps.append({"step": "Error Fetching Reusable Function Codes", "content": str(e)})
            return {"intermediate_steps": intermediate_steps, "final_code": "# Error fetching reusable function codes.", "added_to_database": False}

    reference_function_code = {}
    if reference_functions:
        try:
            reference_function_code = {
                func_name: get_function_wrapper(func_name).get("code", "")
                for func_name in reference_functions
            }
            print(f"[DEBUG] Reference Function Codes: {reference_function_code}")
            intermediate_steps.append({"step": "Fetch Reference Function Codes", "content": reference_function_code})
        except Exception as e:
            print(f"[ERROR] Fetching reference function codes failed: {e}")
            intermediate_steps.append({"step": "Error Fetching Reference Function Codes", "content": str(e)})
            return {"intermediate_steps": intermediate_steps, "final_code": "# Error fetching reference function codes.", "added_to_database": False}

    # Step 3: Use LLM to determine required external APIs based on the user's function description
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
        return {"intermediate_steps": intermediate_steps, "final_code": "# Error during APIResponse analysis.", "added_to_database": False}

    # Step 3.2: Access and parse the API response
    try:
        content = api_response.choices[0].message.content
        print(f"[DEBUG] Raw API Content: {content}")
        api_response_parsed = APIResponse.model_validate_json(content)
        print(f"[DEBUG] Parsed APIResponse: {api_response_parsed}")
        intermediate_steps.append({"step": "Identify External API", "content": api_response_parsed.dict()})

        # Create a list with the single API for consistency with the rest of your code
        external_apis = [api_response_parsed]
    except (ValidationError, IndexError, AttributeError, json.JSONDecodeError) as e:
        print(f"[ERROR] Parsing APIResponse failed: {e}")
        intermediate_steps.append({"step": "Error Parsing APIResponse", "content": str(e)})
        return {"intermediate_steps": intermediate_steps, "final_code": "# Error parsing APIResponse.", "added_to_database": False}

    # Handle cases with no API found (this shouldn't happen with the new structure, but keeping it for safety)
    if not external_apis:
        print("[INFO] No external API required for this function.")

    # Step 4: Handle external API and documentation search
    api_contexts = []
    for api in external_apis:
        api_name = api.name
        search_query = f"{api_name} API documentation python"
        print(f"[DEBUG] Searching for API documentation with query: {search_query}")
        try:
            search_results = serpapi_search_v2(query=search_query)
            # ... rest of your code ...
            print(f"[DEBUG] Search Results for {api_name}: {search_results}")
            intermediate_steps.append({"step": f"Search API Documentation for {api_name}", "content": search_results})
        except Exception as e:
            print(f"[ERROR] serpapi_search_v2 failed for {api_name}: {e}")
            intermediate_steps.append({"step": f"Error Searching API Documentation for {api_name}", "content": str(e)})
            continue  # Skip to the next API

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
            continue  # Skip to the next API

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
            continue  # Skip to the next API

        selected_urls = link_selection_parsed.selected_urls or []
        print(f"[DEBUG] Selected URLs for {api_name}: {selected_urls}")
        scraped_urls = set()
        api_scrape_info = {}


        # Step 5: Scrape and recursively explore additional URLs until there are no more
        while selected_urls:
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

           # Step 6: Use LLM to extract relevant info and identify more URLs to scrape
           extraction_prompt = f"""The user wants to create a function described as follows: {description}.
           You have the following API information scraped from various documentation sources: {json.dumps(api_scrape_info)}.

           Extract the relevant API methods, endpoints, and usage patterns needed to implement the user's function. If any other URLs should be scraped for further information, include them in the 'additional_urls' field."""

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
               "additional_urls": []
           }
           for result in extraction_results:
               try:
                   content = result.choices[0].message.content
                   parsed_result = ExtractionInfo.parse_raw(content)
                   combined_extraction["relevant_info"] += parsed_result.relevant_info + "\n"
                   combined_extraction["additional_urls"].extend(parsed_result.additional_urls)
               except (ValidationError, IndexError, AttributeError, json.JSONDecodeError) as e:
                   print(f"[ERROR] Parsing ExtractionInfo response failed: {e}")
                   intermediate_steps.append({"step": "Error Parsing ExtractionInfo Response", "content": str(e)})

           # Include extracted info in API contexts
           api_contexts.append(combined_extraction["relevant_info"])
           print(f"[DEBUG] Updated API Contexts: {api_contexts}")

           # Queue additional URLs for scraping
           new_urls = [url for url in combined_extraction["additional_urls"] if url not in scraped_urls and is_valid_url(url)]
           print(f"[DEBUG] New URLs to Scrape: {new_urls}")
           selected_urls.extend(new_urls)

   # Step 7: Use all gathered information to generate the final function
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
               2. Complete function code (including the @babyagi.register_function decorator)
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
           return {"intermediate_steps": intermediate_steps, "final_code": "# Error during GeneratedFunction generation.", "added_to_database": False}

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
           combined_final["metadata"].update(parsed_result.metadata)
           combined_final["imports"].extend(parsed_result.imports)
           combined_final["dependencies"].extend(parsed_result.dependencies)
           combined_final["key_dependencies"].extend(parsed_result.key_dependencies)
           combined_final["triggers"].extend(parsed_result.triggers)
       except (ValidationError, IndexError, AttributeError, json.JSONDecodeError) as e:
           print(f"[ERROR] Parsing GeneratedFunction response failed: {e}")
           intermediate_steps.append({"step": "Error Parsing GeneratedFunction Response", "content": str(e)})
           return {"intermediate_steps": intermediate_steps, "final_code": "# Error parsing GeneratedFunction response.", "added_to_database": False}

    # Remove duplicates from lists
    combined_final["imports"] = list({json.dumps(imp): imp for imp in combined_final["imports"]}.values())
    combined_final["dependencies"] = list(set(combined_final["dependencies"]))
    combined_final["key_dependencies"] = list(set(combined_final["key_dependencies"]))
    combined_final["triggers"] = list(set(combined_final["triggers"]))

    print(f"[DEBUG] Combined Final GeneratedFunction: {combined_final}")
    intermediate_steps.append({"step": "Generate Final Function", "content": combined_final})

    # Step 8: Add the generated function to the database
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

   # Return the intermediate steps, the final generated function code, and whether it was added to the database
    return {
       "intermediate_steps": intermediate_steps,
       "final_code": combined_final["code"],
       "added_to_database": success
    }