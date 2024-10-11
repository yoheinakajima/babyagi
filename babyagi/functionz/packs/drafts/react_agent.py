from functionz.core.framework import func

@func.register_function(
    metadata={
        "description": "An agent that takes an input, plans using LLM, executes actions using functions from display_functions_wrapper(), and continues until the task is complete using chain-of-thought techniques while providing detailed reasoning and function execution steps."
    },
    imports=["litellm", "json", "copy"],
    dependencies=["get_function_wrapper", "execute_function_wrapper", "get_all_functions_wrapper"],
    key_dependencies=["OPENAI_API_KEY"]
)
def react_agent(input_text) -> str:
    def map_python_type_to_json(python_type: str) -> dict:
        type_mapping = {
            "str": {"type": "string"},
            "int": {"type": "integer"},
            "float": {"type": "number"},
            "bool": {"type": "boolean"},
            "list": {"type": "array", "items": {"type": "string"}},
            "dict": {"type": "object"},
            "Any": {"type": "string"}
        }
        return type_mapping.get(python_type, {"type": "string"})

    try:
        # Enable verbose logging for LiteLLM
        litellm.set_verbose = True

        # Get available functions using get_all_functions_wrapper
        all_functions = get_all_functions_wrapper()

        # Extract function names from the structured data
        available_function_names = [func_info['name'] for func_info in all_functions]

        # Fetch available functions from the database
        tools = []
        for func_name in available_function_names:
            # Retrieve function details using get_function_wrapper
            function_data = get_function_wrapper(func_name)
            if function_data:
                # Construct the tool definition for LiteLLM
                tool = {
                    "type": "function",
                    "function": {
                        "name": function_data['name'],
                        "description": function_data['metadata'].get('description', ''),
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        },
                    },
                }

                # Map input_parameters to the tool's parameters
                for param in function_data.get('input_parameters', []):
                    json_schema = map_python_type_to_json(param['type'])
                    tool['function']['parameters']['properties'][param['name']] = {
                        **json_schema,
                        "description": param.get('description', '')
                    }
                    if param.get('required', False):
                        tool['function']['parameters']['required'].append(param['name'])

                tools.append(tool)
            else:
                raise ValueError(f"Function '{func_name}' not found in the database.")

        # Initialize function call history
        function_call_history = []

        # Initialize chat context with system message
        system_prompt = (
            "You are an AI assistant that uses a chain-of-thought reasoning process to solve tasks. "
            "Let's think step by step to solve the following problem. "
            "You have access to the following functions which you can use to complete the task. "
            "Explain your reasoning in detail, including any functions you use and their outputs. "
            "At the end of your reasoning, provide the final answer after 'Answer:'. "
            "Before finalizing, review your reasoning for any errors or inconsistencies. "
            "Avoid repeating function calls with the same arguments you've already tried. "
            "Here is the history of function calls you have made so far: {{function_call_history}}"
        )

        chat_context = [
            {"role": "system", "content": system_prompt.replace("{{function_call_history}}", "None")},
            {"role": "user", "content": input_text},
        ]

        # Initialize loop parameters
        max_iterations = 5
        iteration = 0

        full_reasoning_path = ""

        while iteration < max_iterations:
            iteration += 1

            # Update the system prompt with the current function call history
            if function_call_history:
                history_str = "\n".join([
                    f"- {call['function_name']} with arguments {call['arguments']} produced output: {call['output']}"
                    for call in function_call_history
                ])
            else:
                history_str = "None"

            chat_context[0]['content'] = system_prompt.replace("{{function_call_history}}", history_str)

            # Call LiteLLM's completion API with the chat context and tools
            response = litellm.completion(
                model="gpt-4-turbo",
                messages=chat_context,
                tools=tools,
                tool_choice="auto",
                max_tokens=1500,
                temperature=0.7
            )

            # Extract the message from the response
            response_message = response['choices'][0]['message']

            # Append the assistant's message to the chat context and full reasoning path
            chat_context.append(response_message)
            full_reasoning_path += f"\nIteration {iteration}:\n{response_message['content']}\n"

            # Check if the assistant wants to call any functions
            tool_calls = response_message.get('tool_calls', [])

            if tool_calls:
                for tool_call in tool_calls:
                    function_name = tool_call['function']['name']
                    function_args = json.loads(tool_call['function']['arguments'])
                    tool_call_id = tool_call['id']

                    # Check if this function call with these arguments has already been made
                    if any(
                        call['function_name'] == function_name and call['arguments'] == function_args
                        for call in function_call_history
                    ):
                        function_response = f"Function '{function_name}' with arguments {function_args} has already been called. Please try a different approach."
                    else:
                        # Execute the function using execute_function_wrapper
                        try:
                            function_output = execute_function_wrapper(function_name, **function_args)
                            function_call_history.append({
                                'function_name': function_name,
                                'arguments': function_args,
                                'output': function_output
                            })
                            function_response = f"Function '{function_name}' executed successfully with output: {function_output}"
                        except Exception as e:
                            function_response = f"Error executing function '{function_name}': {str(e)}"

                    # Ensure function_response is a string
                    if not isinstance(function_response, str):
                        function_response = json.dumps(function_response)

                    # Append the function response to the chat context and full reasoning path
                    chat_context.append({
                        "tool_call_id": tool_call_id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response
                    })
                    full_reasoning_path += f"Function Call: {function_name}\nArguments: {function_args}\nOutput: {function_response}\n"

                # Continue the loop to allow the assistant to process the function outputs
                continue
            else:
                # No function calls, assume task is complete
                break

        # Extract the final answer from the last assistant message
        final_answer = response_message['content'].split('Answer:')[-1].strip() if 'Answer:' in response_message['content'] else response_message['content']

        # Compile the full response including reasoning steps and function call history
        if function_call_history:
            function_calls_str = "\n".join([
                f"Function '{call['function_name']}' called with arguments {call['arguments']}, produced output: {call['output']}"
                for call in function_call_history
            ])
        else:
            function_calls_str = "No functions were called."

        full_response = (
            f"Full Reasoning Path:\n{full_reasoning_path}\n\n"
            f"Functions Used:\n{function_calls_str}\n\n"
            f"Final Answer:\n{final_answer}"
        )

        return full_response

    except Exception as e:
        return f"An error occurred: {str(e)}\n\nFull reasoning path so far:\n{full_reasoning_path}"