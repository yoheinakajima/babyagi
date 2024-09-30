import babyagi

@babyagi.register_function(
    metadata={"description": "Executes AI-generated Python code in a secure E2B sandbox."},
    imports=["e2b_code_interpreter"],
    key_dependencies=["e2b_api_key"]
)
def execute_code_in_sandbox(code: str):
    """
    This function initializes an E2B sandbox and executes AI-generated Python code within it.

    :param code: Python code to be executed.
    :return: Results and logs from the code execution.
    """
    from e2b_code_interpreter import CodeInterpreter
  
    with CodeInterpreter() as sandbox:
        # Execute the code in the sandbox
        execution = sandbox.notebook.exec_cell(code)

        # Handle execution errors
        if execution.error:
            return {"error": execution.error.name, "message": execution.error.value, "traceback": execution.error.traceback}

        # Gather results
        results = [{"text": result.text, "formats": result.formats()} for result in execution.results]
        logs = {"stdout": execution.logs.stdout, "stderr": execution.logs.stderr}

        return {"results": results, "logs": logs}


# Function 2: Chat with LLM (OpenAI) and parse response to execute in sandbox

@babyagi.register_function(
    metadata={"description": "Calls the OpenAI API (gpt-3.5-turbo) to generate code and execute it in an E2B sandbox."},
    imports=["litellm", "os"],
    key_dependencies=["openai_api_key"],
    dependencies=["execute_code_in_sandbox"]
)
def chat_with_llm_and_execute(user_message: str):
    """
    This function calls the OpenAI API (via litellm) to generate Python code based on the user's message,
    then executes that code in an E2B sandbox.

    :param user_message: The message to prompt the LLM with.
    :return: Results from the executed code and logs.
    """
    from litellm import completion
  
    # Load OpenAI API key from environment
    api_key = globals()['openai_api_key']

    # Define the message for the LLM
    messages = [{"role": "user", "content": user_message}]

    # Call the LLM using litellm completion method
    response = completion(model="gpt-3.5-turbo", messages=messages)
    llm_generated_code = response['choices'][0]['message']['content']

    # Execute the generated code in the E2B sandbox
    return execute_code_in_sandbox(llm_generated_code)


# Function 3: Save generated charts

@babyagi.register_function(
    metadata={"description": "Saves a base64-encoded PNG chart to a file."},
    imports=["base64"],
)
def save_chart(base64_png: str, filename: str = "chart.png"):
    """
    Saves a base64-encoded PNG chart to a file.

    :param base64_png: Base64-encoded PNG data.
    :param filename: The name of the file to save the chart.
    :return: The path to the saved chart.
    """
    png_data = base64.b64decode(base64_png)

    # Save the decoded PNG to a file
    with open(filename, "wb") as file:
        file.write(png_data)

    return f"Chart saved to {filename}"


# Function 4: Execute main flow (chat with LLM, run code, save chart if exists)

@babyagi.register_function(
    metadata={"description": "Main function to prompt LLM, execute code in E2B, and save any generated charts."},
    dependencies=["chat_with_llm_and_execute", "save_chart"]
)
def e2b_llm_to_chart(user_message: str):
    """
    The main workflow function: sends a message to the LLM, executes the generated code, and saves any charts.

    :param user_message: The user's input prompt for the LLM.
    :return: Final results and path to saved chart if applicable.
    """
    # Get code execution results and logs
    execution_results = chat_with_llm_and_execute(user_message)

    # Check if any chart (PNG) was generated
    if execution_results["results"]:
        for result in execution_results["results"]:
            if "png" in result["formats"]:
                # Save the chart if PNG format is present
                chart_filename = save_chart(result["formats"]["png"])
                return {"execution_results": execution_results, "chart_saved_to": chart_filename}

    return {"execution_results": execution_results}
