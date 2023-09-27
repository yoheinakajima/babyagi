from skills.skill import Skill
import openai
import os
import requests
from urllib.parse import quote  # Python built-in URL encoding function

#This Airtable Skill is tuned to work with our Airtable set up, where we are seaeching a specific column in a specific table, in a specific base. ll three variables need to be set below (Lines 55-59)
class AirtableSearch(Skill):
    name = 'airtable_search'
    description = "A skill that retrieves data from our Airtable notes using a search. Useful for remembering who we talked to about a certain topic."
    api_keys_required = ['code_reader','skill_saver','documentation_search','text_completion']

    def __init__(self, api_keys, main_loop_function):
        super().__init__(api_keys, main_loop_function)

    def execute(self, params, dependent_task_outputs, objective):
        if not self.valid:
            return

        # Initialize a list to keep track of queries tried
        tried_queries = []

        # Modify the query based on the dependent task output
        if dependent_task_outputs != "":
            dependent_task = f"Use the dependent task output below as reference to help craft the correct search query for the provided task above. Dependent task output:{dependent_task_outputs}."
        else:
            dependent_task = "."
        
        # Initialize output
        output = ''
        
        while not output: 
            # If there are tried queries, add them to the prompt
            tried_queries_prompt = f" Do not include search queries we have tried, and instead try synonyms or misspellings. Search queries we have tried: {', '.join(tried_queries)}." if tried_queries else ""
            print(tried_queries_prompt)
            query = self.text_completion_tool(f"You are an AI assistant tasked with generating a one word search query based on the following task: {params}. Provide only the search query as a response. {tried_queries_prompt} Take into account output from the previous task:{dependent_task}.\nExample Task: Retrieve data from Airtable notes using the skill 'airtable_search' to find people we have talked to about TED AI.\nExample Query:TED AI\nExample Task:Conduct a search in our Airtable notes to identify investors who have expressed interest in climate.\nExample Query:climate\nTask:{params}\nQuery:")

            # Add the query to the list of tried queries
            tried_queries.append(query)

            print("\033[90m\033[3m"+"Search query: " +str(query)+"\033[0m")

            # Retrieve the Airtable API key
            airtable_api_key = self.api_keys['airtable']
          
            # Set the headers for the API request
            headers = {
                "Authorization": f"Bearer {airtable_api_key}",
                "Content-Type": "application/json"
            }
          

            # Set base id
            base_id = '<base_id>'
            table_name = '<table_name'


            # The field to filter on and the value to search for
            filter_field = '<filter_field>' 
            filter_value = query

            # URL encode the filter_field
            encoded_filter_field = quote(filter_field)

            # If filter_field contains a space, wrap it in curly brackets
            formula_field = f'{{{filter_field}}}' if ' ' in filter_field else f'{filter_field}'

            # Construct the Airtable formula and URL encode it
            formula = f'"{filter_value}",{formula_field}'
            encoded_formula = quote(formula)

            # Construct the Airtable API URL
            url = f"https://api.airtable.com/v0/{base_id}/{table_name}?fields%5B%5D={encoded_filter_field}&filterByFormula=FIND({encoded_formula})"
            print(url)
        

            # Make the API request to retrieve the data from Airtable
            response = requests.get(url, headers=headers)

            # Check if the API request was successful
            if response.status_code == 200:
                data = response.json()
                
                # Iterate through the records and process each one
                for record in data['records']:
                    # Combine objective, task, and record into a single string
                    input_str = f"Your objective:{objective}\nYour task:{params}\nThe Airtable record:{record['fields']}"
                    #print(record['fields'])
                  
                    if output == "":
                      instructions = ""
                    else:
                      instructions = f"Update the existing summary by adding information from this new record. ###Current summary:{output}."
                    
                    # Send the combined string to the OpenAI ChatCompletion API
                    response = self.text_completion_tool(f"You are an AI assistant that will review content from an Airtable record provided by the user, and extract only relevant information to the task at hand with context on why that information is relevant, taking into account the objective. If there is no relevant info, simply respond with '###'. Note that the Airtable note may use shorthand, and do your best to understand it first.{instructions} #####AIRTABLE DATA: {input_str}.") 
                    print("\033[90m\033[3m" +str(response)+"\033[0m")
                    output += response + "\n####"
            else:
                print(f"Failed to retrieve data from Airtable. Status code: {response.status_code}")
                return None

        # Return the combined output
      
        output = "Tried Queries: "+str(tried_queries)+"###Result:"+output
        return output


    def text_completion_tool(self, prompt: str):
        messages = [
            {"role": "user", "content": prompt}
        ]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=messages,
            temperature=0.2,
            max_tokens=350,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
    
        return response.choices[0].message['content'].strip()
