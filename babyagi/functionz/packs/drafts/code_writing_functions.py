from functionz.core.framework import func

@func.register_function(
  metadata={"description": "Checks if an existing function satisfies the user input"},
  dependencies=["gpt_call", "get_all_functions_wrapper"]
)
def check_existing_functions(user_input):
  import json

  while True:
      # Get all functions and their descriptions
      functions = get_all_functions_wrapper()
      function_descriptions = [
          {"name": f['name'], "description": f['metadata'].get('description', '')}
          for f in functions
      ]

      # Prepare the prompt
      prompt = f"""
You are an expert software assistant. The user has provided the following request:

"{user_input}"

Below is a list of available functions with their descriptions:

{function_descriptions}

Determine if any of the existing functions perfectly fulfill the user's request. If so, return the name of the function.

Provide your answer in the following JSON format:
{{
  "function_found": true or false,
  "function_name": "<name of the function if found, else null>"
}}

Examples:

Example 1:
User input: "Calculate the sum of two numbers"
Functions: [{{"name": "add_numbers", "description": "Adds two numbers"}}]
Response:
{{
  "function_found": true,
  "function_name": "add_numbers"
}}

Example 2:
User input: "Translate text to French"
Functions: [{{"name": "add_numbers", "description": "Adds two numbers"}}]
Response:
{{
  "function_found": false,
  "function_name": null
}}

Now, analyze the user's request and provide the JSON response.
"""

      response = gpt_call(prompt)

      # Try to parse the JSON response
      try:
          result = json.loads(response)
          if 'function_found' in result and isinstance(result['function_found'], bool) and \
             ('function_name' in result):
              return result
          else:
              raise ValueError("Invalid JSON structure")
      except Exception as e:
          # If parsing fails, retry
          continue

@func.register_function(
  metadata={"description": "Breaks down the user task into smaller functions"},
  dependencies=["gpt_call"]
)
def break_down_task(user_input):
  import json
  while True:
      # Prepare the prompt with detailed context
      prompt = f"""
You are an expert software assistant helping to break down a user's request into smaller functions for a microservice-inspired architecture. The system is designed to be modular, with each function being small and designed optimally for potential future reuse.

When breaking down the task, consider the following:

- Each function should be as small as possible and do one thing well.
- Use existing functions where possible. You have access to functions such as 'gpt_call', 'find_similar_function', and others in our function database.
- Functions can depend on each other. Use 'dependencies' to specify which functions a function relies on.
- Functions should include appropriate 'imports' if external libraries are needed.
- Provide the breakdown as a list of functions, where each function includes its 'name', 'description', 'input_parameters', 'output_parameters', 'dependencies', and 'code' (just a placeholder or brief description at this stage).
- Make sure descriptions are detailed so an engineer could build it to spec.
- Every sub function you create should be designed to be reusable by turning things into parameters, vs hardcoding them.

User request:

"{user_input}"

Provide your answer in JSON format as a list of functions. Each function should have the following structure:

{{
  "name": "function_name",
  "description": "Brief description of the function",
  "input_parameters": [{{"name": "param1", "type": "type1"}}, ...],
  "output_parameters": [{{"name": "output", "type": "type"}}, ...],
  "dependencies": ["dependency1", "dependency2", ...],
  "imports": ["import1", "import2", ...],
  "code": "Placeholder or brief description"
}}

Example:

[
  {{
      "name": "process_data",
      "description": "Processes input data",
      "input_parameters": [{{"name": "data", "type": "str"}}],
      "output_parameters": [{{"name": "processed_data", "type": "str"}}],
      "dependencies": [],
      "imports": [],
      "code": "Placeholder for process_data function"
  }},
  {{
      "name": "analyze_data",
      "description": "Analyzes processed data",
      "input_parameters": [{{"name": "processed_data", "type": "str"}}],
      "output_parameters": [{{"name": "analysis_result", "type": "str"}}],
      "dependencies": ["process_data"],
      "imports": [],
      "code": "Placeholder for analyze_data function"
  }}
]

Now, provide the breakdown for the user's request.
"""

      response = gpt_call(prompt)

      # Try to parse the JSON response
      try:
          functions = json.loads(response)
          # Basic validation of the structure
          if isinstance(functions, list) and all('name' in func and 'description' in func for func in functions):
              return functions
          else:
              raise ValueError("Invalid JSON structure")
      except Exception as e:
          # If parsing fails, retry
          continue

@func.register_function(
  metadata={"description": "Decides if imports or external APIs are needed"},
  dependencies=["gpt_call", "get_all_functions_wrapper"]
)
def decide_imports_and_apis(context):
  import json
  while True:
      # Get all available functions and their imports
      all_functions = get_all_functions_wrapper()
      existing_imports = set()
      for func in all_functions:
          existing_imports.update(func.get('imports', []))

      # Prepare the prompt
      prompt = f"""
You are an expert software assistant helping to decide what imports and external APIs are needed for a set of functions based on the context provided.

Context:

{context}

Existing standard Python imports:

{list(existing_imports)}

Determine the libraries (imports) and external APIs needed for these functions. Separate standard Python libraries from external libraries or APIs.

Provide your answer in the following JSON format:

{{
  "standard_imports": ["import1", "import2", ...],
  "external_imports": ["external_import1", "external_import2", ...],
  "external_apis": ["api1", "api2", ...],
  "documentation_needed": [
      {{"name": "external_import1", "type": "import" or "api"}},
      ...
  ]
}}

Note: 'documentation_needed' should include any external imports or APIs for which documentation should be looked up.

Example:

{{
  "standard_imports": ["os", "json"],
  "external_imports": ["requests"],
  "external_apis": ["SerpAPI"],
  "documentation_needed": [
      {{"name": "requests", "type": "import"}},
      {{"name": "SerpAPI", "type": "api"}}
  ]
}}

Now, analyze the context and provide the JSON response.
"""

      response = gpt_call(prompt)

      # Try to parse the JSON response
      try:
          result = json.loads(response)
          # Basic validation of the structure
          if all(key in result for key in ['standard_imports', 'external_imports', 'external_apis', 'documentation_needed']):
              return result
          else:
              raise ValueError("Invalid JSON structure")
      except Exception as e:
          # If parsing fails, retry
          continue

@func.register_function(
  metadata={"description": "Gets functions that depend on a given function"},
  dependencies=["get_all_functions_wrapper"]
)
def get_functions_that_depend_on(function_name):
  all_functions = get_all_functions_wrapper()
  dependent_functions = []
  for function in all_functions:
      if function_name in function.get('dependencies', []):
          dependent_functions.append(function['name'])
  return dependent_functions


@func.register_function(
    metadata={"description": "Generates the function code using LLM"},
    dependencies=["gpt_call", "get_function_wrapper", "get_functions_that_depend_on", "get_all_functions_wrapper"]
)
def generate_function_code(function, context):
    while True:

        print("\033[1;32mGenerating code for function: ", function["name"], "\033[0m")
        # Gather dependent functions and their code
        dependencies = function.get('dependencies', [])
        dependency_code = ''
        for dep in dependencies:
            dep_function = get_function_wrapper(dep)
            if dep_function:
                dependency_code += f"\n# Code for dependency function '{dep}':\n{dep_function['code']}\n"

        # Gather functions that depend on the same imports
        imports = function.get('imports', [])
        functions_with_same_imports = []
        all_functions = get_all_functions_wrapper()
        for func_with_imports in all_functions:
            if set(func_with_imports.get('imports', [])) & set(imports):
                functions_with_same_imports.append(func_with_imports)

        similar_imports_functions_code = ''
        for func_with_imports in functions_with_same_imports:
            similar_imports_functions_code += f"\n# Code for function '{func_with_imports['name']}' that uses similar imports:\n{func_with_imports['code']}\n"

        # Prepare the prompt
        prompt = f"""
You are an expert Python programmer. Your task is to write detailed and working code for the following function based on the context provided. Do not provide placeholder code, but rather do your best like you are the best senior engineer in the world and provide the best code possible. DO NOT PROVIDE PLACEHOLDER CODE.

Function details:

Name: {function['name']}
Description: {function['description']}
Input parameters: {function['input_parameters']}
Output parameters: {function['output_parameters']}
Dependencies: {function['dependencies']}
Imports: {function['imports']}

Overall context:

{context}

Dependency code:

{dependency_code}

Code from functions with similar imports:

{similar_imports_functions_code}

Please provide the function details in JSON format, following this structure:

{{
  "function_name": "<function_name>",
  "metadata": {{
    "description": "<function_description>",
    "input_parameters": {function['input_parameters']},
    "output_parameters": {function['output_parameters']}
  }},
  "code": "<function_code_as_string>",
  "imports": {function['imports']},
  "dependencies": {function['dependencies']},
  "key_dependencies": [],
  "triggers": []
}}

**Example JSON Output:**

{{
  "function_name": "example_function",
  "metadata": {{
    "description": "An example function.",
    "input_parameters": [{{"name": "param1", "type": "str"}}],
    "output_parameters": [{{"name": "result", "type": "str"}}]
  }},
  "code": "<complete function code goes here>",
  "imports": ["os"],
  "dependencies": [],
  "key_dependencies": [],
  "triggers": []
}}

Provide the JSON output only, without any additional text. Do not provide placeholder code, but write complete code that is ready to run and provide the expected output.

Now, please provide the JSON output for the function '{function['name']}'.
"""

        response = gpt_call(prompt)

        try:
            # Parse the JSON response
            import json
            function_data = json.loads(response)

            # Return the parsed function data
            return function_data
        except json.JSONDecodeError as e:
            # If parsing fails, retry
            print(f"JSON decoding error: {str(e)}")
            continue
        except Exception as e:
            print(f"Error processing function data: {str(e)}")
            return None


@func.register_function(
    metadata={"description": "Creates a new function if similar functions are not sufficient"},
    dependencies=["decide_imports_and_apis", "generate_function_code","add_new_function"]
)
def create_function(function, context):
    # Decide imports and APIs
    imports_and_apis = decide_imports_and_apis(context)
    function['imports'] = imports_and_apis.get('standard_imports', []) + imports_and_apis.get('external_imports', [])

    # Update context with imports and APIs
    context.update({'imports_and_apis': imports_and_apis})

    # Generate function code
    function_data = generate_function_code(function, context)

    if function_data:
        # Register the function using the parsed JSON data
        add_new_function(
            name=function_data['function_name'],
            code=function_data['code'],
            metadata=function_data['metadata'],
            imports=function_data.get('imports', []),
            dependencies=function_data.get('dependencies', []),
            key_dependencies=function_data.get('key_dependencies', []),
            triggers=function_data.get('triggers', [])
        )

        #print(f"Function '{function_data['function_name']}' registered successfully.")

        return {
            'name': function_data['function_name'],
            'code': function_data['code'],
            'metadata': function_data['metadata'],
            'imports': function_data.get('imports', []),
            'dependencies': function_data.get('dependencies', []),
            'key_dependencies': function_data.get('key_dependencies', []),
            'triggers': function_data.get('triggers', [])
        }
    else:
        print("Failed to generate function code.")
        return None



@func.register_function(
  metadata={"description": "Generates the required functions based on the breakdown"},
  dependencies=["find_similar_function", "create_function", "get_function_wrapper"]
)
def generate_functions(function_breakdown, context):
  for function in function_breakdown:
      function_name = function['name']
      # Find similar functions
      similar_functions = find_similar_function(function['description'])
      function_found = False
      for similar_function_name in similar_functions:
          similar_function = get_function_wrapper(similar_function_name)
          if similar_function and similar_function['metadata'].get('description', '') == function['description']:
              function_found = True
              break
      if not function_found:
          # Combine context for this function
          function_context = context.copy()
          function_context.update({'function': function})
          create_function(function, function_context)

@func.register_function(
  metadata={"description": "Runs the final function to produce the output for the user"},
  dependencies=["func"]
)
def run_final_function(function_name, *args, **kwargs):
  result = func.execute_function(function_name, *args, **kwargs)
  return result

@func.register_function(
    metadata={"description": "Extracts parameters from user input for a given function"},
    dependencies=["gpt_call", "get_function_wrapper"]
)
def extract_function_parameters(user_input, function_name):
    import json
    # Get the function code and parameters
    function = get_function_wrapper(function_name)
    if not function:
        print(f"Function '{function_name}' not found.")
        return None

    # Prepare the prompt to convert user input into function parameters
    while True:
        prompt = f"""
You are an expert assistant. The user wants to execute the following function:

Function code:
{function['code']}

Function description:
{function['metadata'].get('description', '')}

Function parameters:
{function['metadata'].get('input_parameters', [])}

The user has provided the following input:
"{user_input}"

Your task is to extract the required parameters from the user's input and provide them in JSON format that matches the function's parameters.

Provide your answer in the following JSON format:
{{
  "parameters": {{
    "param1": value1,
    "param2": value2,
    ...
  }}
}}

Ensure that the parameters match the function's required input parameters.

Examples:

Example 1:

Function code:
def add_numbers(a, b):
    return a + b

Function parameters:
[{{"name": "a", "type": "int"}}, {{"name": "b", "type": "int"}}]

User input: "Add 5 and 3"

Response:
{{
  "parameters": {{
    "a": 5,
    "b": 3
  }}
}}

Example 2:

Function code:
def greet_user(name):
    return f"Hello, {{name}}!"

Function parameters:
[{{"name": "name", "type": "str"}}]

User input: "Say hello to Alice"

Response:
{{
  "parameters": {{
    "name": "Alice"
  }}
}}

Now, using the function provided and the user's input, extract the parameters and provide the JSON response.
"""
        response = gpt_call(prompt)

        # Try to parse the JSON response
        try:
            result = json.loads(response)
            if 'parameters' in result and isinstance(result['parameters'], dict):
                return result['parameters']
            else:
                raise ValueError("Invalid JSON structure")
        except Exception as e:
            # If parsing fails, retry
            continue

@func.register_function(
    metadata={"description": "Main function to process user input and generate the required functions"},
    dependencies=["check_existing_functions", "break_down_task", "generate_functions", "run_final_function", "extract_function_parameters"]
)
def process_user_input(user_input):
    # First, check if an existing function satisfies the user input
    print("\033[1;95mProcessing user input: ", user_input, "\033[0m")
    result = check_existing_functions(user_input)
    if result['function_found']:
        function_name = result['function_name']
    else:
        # Break down the task into functions
        function_breakdown = break_down_task(user_input)
        # Context to be passed around
        context = {'user_input': user_input, 'function_breakdown': function_breakdown}
        # Generate the required functions
        generate_functions(function_breakdown, context)
        # Assume the main function is the first one in the breakdown
        function_name = function_breakdown[0]['name']

    # Extract parameters from user input for the function
    parameters = extract_function_parameters(user_input, function_name)
    if parameters is None:
        print("Failed to extract parameters from user input.")
        return None

    # Call the function with the parameters
    output = run_final_function(function_name, **parameters)
    return output


