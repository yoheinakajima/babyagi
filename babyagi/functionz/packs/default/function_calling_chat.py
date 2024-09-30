from functionz.core.framework import func
import json
import litellm

# Assuming `func` is the registry from your framework
# and `execute_function_wrapper` is already registered in the database.

@func.register_function(
    metadata={
        "description": "A chat application that interacts with LiteLLM and executes selected functions from the database."
    },
    imports=["litellm", "json"],
    dependencies=["get_function_wrapper", "execute_function_wrapper"],
    key_dependencies=["OPENAI_API_KEY"]  # Ensure this key is set in your environment
)
def chat_with_functions(chat_history, available_function_names) -> str:
    def map_python_type_to_json(python_type: str) -> dict:
        """
        Maps Python type annotations to JSON Schema types.

        Args:
            python_type (str): The Python type as a string.

        Returns:
            dict: The corresponding JSON Schema type with additional details if necessary.
        """
        type_mapping = {
            "str": {"type": "string"},
            "int": {"type": "integer"},
            "float": {"type": "number"},
            "bool": {"type": "boolean"},
            "list": {"type": "array", "items": {"type": "string"}},  # Assuming list of strings
            "dict": {"type": "object"},
            "Any": {"type": "string"}  # Default to string for unsupported types
        }
        return type_mapping.get(python_type, {"type": "string"})

    # Enable verbose logging for LiteLLM
    litellm.set_verbose = True

    # Initialize chat context with system message
    chat_context = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

    # Validate and append chat history
    if not isinstance(chat_history, list):
        raise ValueError("chat_history must be a list of messages.")

    for message in chat_history:
        if not isinstance(message, dict):
            raise ValueError("Each message in chat_history must be a dictionary.")
        role = message.get('role')
        content = message.get('message')
        if role not in ['user', 'assistant', 'system']:
            raise ValueError("Message role must be 'user', 'assistant', or 'system'.")
        if not isinstance(content, str):
            raise ValueError("Message content must be a string.")
        chat_context.append({"role": role, "content": content})

    # Handle available_function_names input
    if isinstance(available_function_names, str):
        # Split the string by commas and strip whitespace
        available_function_names = [name.strip() for name in available_function_names.split(',') if name.strip()]
    elif isinstance(available_function_names, list):
        # Ensure all elements are strings and strip whitespace
        available_function_names = [name.strip() for name in available_function_names if isinstance(name, str) and name.strip()]
    else:
        raise ValueError("available_function_names must be a string or a list of strings.")

    if not available_function_names:
        raise ValueError("No valid function names provided in available_function_names.")

    # Fetch available functions from the database
    tools = []
    for func_name in available_function_names:
        # Retrieve function details using the get_function_wrapper
        function_data = get_function_wrapper(func_name)
        if function_data:
            # Construct the tool definition for LiteLLM
            tool = {
                "type": "function",
                "function": {
                    "name": function_data['name'],
                    "description": function_data['metadata']['description'],
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    },
                },
            }

            # Map input_parameters to the tool's parameters
            for param in function_data.get('input_parameters', []):
                # Convert Python types to JSON Schema types
                json_schema = map_python_type_to_json(param['type'])
                tool['function']['parameters']['properties'][param['name']] = {
                    **json_schema,
                    "description": param.get('description', '')
                }
                if param.get('required', False):
                    tool['function']['parameters']['required'].append(param['name'])

            tools.append(tool)
        else:
            # Handle the case where the function is not found
            raise ValueError(f"Function '{func_name}' not found in the database.")


    # Call LiteLLM's completion API with the user message and available tools
    response = litellm.completion(
        model="gpt-4-turbo",
        messages=chat_context,
        tools=tools,
        tool_choice="auto"
    )

    # Extract the message from the response
    response_message = response['choices'][0]['message']

    # Check if the model wants to call any functions
    tool_calls = response_message.get('tool_calls', [])

    # If there are function calls, execute them
    if tool_calls:
        # Append the assistant's message to the chat context
        chat_context.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call['function']['name']
            function_args = json.loads(tool_call['function']['arguments'])
            tool_call_id = tool_call['id']  # Extract the tool_call_id

            # Execute the function using execute_function_wrapper
            try:
                function_response = execute_function_wrapper(function_name, **function_args)
            except Exception as e:
                function_response = f"Error executing function '{function_name}': {str(e)}"

            # Ensure function_response is a string
            if not isinstance(function_response, str):
                function_response = json.dumps(function_response)

            # Append the function response to the chat context
            chat_context.append({
                "tool_call_id": tool_call_id,  # Include the tool_call_id
                "role": "tool",  # Use 'tool' as per LiteLLM's protocol
                "name": function_name,
                "content": function_response
            })

        # Call LiteLLM again with the updated context including function responses
        second_response = litellm.completion(
            model="gpt-4-turbo",
            messages=chat_context
        )

        # Extract and return the assistant's final response
        assistant_response = second_response['choices'][0]['message']['content']
        return assistant_response
    else:
        # If no functions are called, return the assistant's message directly
        assistant_response = response_message.get('content', '')
        return assistant_response
