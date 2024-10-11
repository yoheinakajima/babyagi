from functionz.core.framework import func

@func.register_function(
    metadata={"description": "Choose or create a function based on user input and execute it."},
    dependencies=[
        "display_functions_wrapper",
        "get_function_wrapper",
        "execute_function_wrapper",
        "generate_function_from_description"
    ],
    imports=[
        {"name": "litellm", "lib": "litellm"},
        {"name": "pydantic", "lib": "pydantic"},
        {"name": "typing", "lib": "typing"},
        {"name": "json", "lib": "json"},
    ]
)
def choose_or_create_function(user_input: str) -> dict:
    """
    Takes user input, compares against existing functions, decides whether to use an existing function or generate a new one, then executes the function with generated parameters.

    Args:
        user_input (str): The user's input or request.

    Returns:
        dict: A dictionary containing the result of the function execution, intermediate steps, and any relevant information.
    """
    from litellm import completion
    from pydantic import BaseModel, Field, ValidationError
    from typing import List, Optional, Dict, Any
    import json

    intermediate_steps = []

    # Step 1: Fetch existing functions
    try:
        existing_functions = display_functions_wrapper()
        print(f"[DEBUG] Existing Functions: {existing_functions}")
        intermediate_steps.append({"step": "Fetch Existing Functions", "content": existing_functions})
    except Exception as e:
        print(f"[ERROR] Failed to fetch existing functions: {e}")
        intermediate_steps.append({"step": "Error Fetching Existing Functions", "content": str(e)})
        return {"intermediate_steps": intermediate_steps, "error": "# Error fetching existing functions."}

    # Step 2: Use LLM to decide whether to use an existing function or generate a new one
    system_prompt = """
You are an assistant that helps decide whether an existing function can fulfill a user's request or if a new function needs to be created.

Please analyze the user's input and the list of available functions.

Return your decision in the following JSON format:

{
    "use_existing_function": true or false,
    "function_name": "name of the existing function" (if applicable),
    "function_description": "description of the function to generate" (if applicable)
}

Provide only the JSON response, without any additional text.
"""

    class FunctionDecision(BaseModel):
        use_existing_function: bool = Field(..., description="True if an existing function can be used; False if a new function needs to be generated.")
        function_name: Optional[str] = Field(None, description="Name of the existing function to use.")
        function_description: Optional[str] = Field(None, description="Description of the new function to generate.")

    decision_prompt = f"""
The user has provided the following input:
\"{user_input}\"

Available Functions:
{existing_functions}
"""

    try:
        decision_response = completion(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": decision_prompt}
            ],
            response_format=FunctionDecision
        )
        print(f"[DEBUG] Decision Response: {decision_response}")
    except Exception as e:
        print(f"[ERROR] LLM call for FunctionDecision failed: {e}")
        intermediate_steps.append({"step": "Error in FunctionDecision LLM Call", "content": str(e)})
        return {"intermediate_steps": intermediate_steps, "error": "# Error during function decision analysis."}

    # Parse the response
    try:
        content = decision_response.choices[0].message.content
        print(f"[DEBUG] Raw Decision Content: {content}")
        decision_parsed = FunctionDecision.parse_raw(content)
        print(f"[DEBUG] Parsed FunctionDecision: {decision_parsed}")
        intermediate_steps.append({"step": "Function Decision", "content": decision_parsed.dict()})
    except (ValidationError, IndexError, AttributeError, json.JSONDecodeError) as e:
        print(f"[ERROR] Parsing FunctionDecision response failed: {e}")
        intermediate_steps.append({"step": "Error Parsing FunctionDecision Response", "content": str(e)})
        return {"intermediate_steps": intermediate_steps, "error": "# Error parsing FunctionDecision response."}

    if decision_parsed.use_existing_function and decision_parsed.function_name:
        function_name = decision_parsed.function_name
        print(f"[INFO] Using existing function: {function_name}")
    elif not decision_parsed.use_existing_function and decision_parsed.function_description:
        # Generate the new function
        print(f"[INFO] Generating new function based on description.")
        gen_result = generate_function_from_description(decision_parsed.function_description)
        intermediate_steps.extend(gen_result.get("intermediate_steps", []))
        if not gen_result.get("added_to_database"):
            print(f"[ERROR] Failed to generate and add new function.")
            return {"intermediate_steps": intermediate_steps, "error": "# Error generating new function."}
        # Get the function name from the generated function code
        function_name = gen_result.get("function_name")
        if not function_name:
            # Extract function name from the code
            import re
            match = re.search(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', gen_result.get("final_code", ""))
            if match:
                function_name = match.group(1)
                print(f"[INFO] Extracted function name: {function_name}")
            else:
                print(f"[ERROR] Function name not found in generated code.")
                return {"intermediate_steps": intermediate_steps, "error": "# Function name not found in generated code."}
    else:
        print(f"[ERROR] Invalid decision or missing information.")
        return {"intermediate_steps": intermediate_steps, "error": "# Invalid function decision."}

    # Step 3: Get the function code using get_function_wrapper
    try:
        function_info = get_function_wrapper(function_name)
        if not function_info:
            print(f"[ERROR] Function {function_name} not found.")
            intermediate_steps.append({"step": "Error Fetching Function", "content": f"Function {function_name} not found."})
            return {"intermediate_steps": intermediate_steps, "error": f"# Function {function_name} not found."}
        print(f"[DEBUG] Function Info: {function_info}")
        intermediate_steps.append({"step": "Fetch Function Info", "content": function_info})
    except Exception as e:
        print(f"[ERROR] Fetching function info failed: {e}")
        intermediate_steps.append({"step": "Error Fetching Function Info", "content": str(e)})
        return {"intermediate_steps": intermediate_steps, "error": "# Error fetching function info."}

    # Step 4: Use LLM to generate parameters for the function based on user input
    param_prompt = f"""
    The user has provided the following input:
    \"{user_input}\"

    The function to execute is:
    {function_info.get('code', '')}

    Generate a JSON object with a single key "parameters" that contains the parameters required by the function, filled in appropriately based on the user's input.

    Return only the JSON object, with no additional text.
    """

    try:
        # Define a Pydantic model with a fixed field "parameters"
        class FunctionParameters(BaseModel):
            parameters: Dict[str, Any]

            class Config:
                extra = 'forbid'  # This sets 'additionalProperties' to False

        param_response = completion(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an assistant that provides only JSON-formatted data, with no additional text."},
                {"role": "user", "content": param_prompt}
            ],
            response_format=FunctionParameters  # Keep the same parsing format
        )
        print(f"[DEBUG] Parameter Response: {param_response}")
    except Exception as e:
        print(f"[ERROR] LLM call for parameter generation failed: {e}")
        intermediate_steps.append({"step": "Error in Parameter Generation LLM Call", "content": str(e)})
        return {"intermediate_steps": intermediate_steps, "error": "# Error generating parameters."}

    # Parse the response using the Pydantic model
    try:
        content = param_response.choices[0].message.content
        print(f"[DEBUG] Raw Parameter Content: {content}")
        function_params_model = FunctionParameters.parse_raw(content)
        function_params = function_params_model.parameters  # Extract the parameters dictionary
        print(f"[DEBUG] Parsed Parameters: {function_params}")
        intermediate_steps.append({"step": "Generate Function Parameters", "content": function_params})
    except (ValidationError, IndexError, AttributeError, json.JSONDecodeError) as e:
        print(f"[ERROR] Parsing parameters failed: {e}")
        intermediate_steps.append({"step": "Error Parsing Parameters", "content": str(e)})
        return {"intermediate_steps": intermediate_steps, "error": "# Error parsing function parameters."}

    # Step 5: Execute the function using execute_function_wrapper
    try:
        # Ensure that function_params is a dictionary
        if not isinstance(function_params, dict):
            raise TypeError("function_params must be a dictionary")
        execution_result = execute_function_wrapper(function_name, **function_params)
        print(f"[DEBUG] Execution Result: {execution_result}")
        intermediate_steps.append({"step": "Execute Function", "content": execution_result})
    except Exception as e:
        print(f"[ERROR] Function execution failed: {e}")
        intermediate_steps.append({"step": "Error Executing Function", "content": str(e)})
        return {"intermediate_steps": intermediate_steps, "error": "# Error executing function."}

    return {
        "intermediate_steps": intermediate_steps,
        "execution_result": execution_result
    }