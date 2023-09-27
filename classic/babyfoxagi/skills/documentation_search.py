
from skills.skill import Skill
from serpapi import GoogleSearch
import openai
from bs4 import BeautifulSoup
import requests
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
}

class DocumentationSearch(Skill):
    name = 'documentation_search'
    description = 'A tool that performs a web search for finding documentation.'
    api_keys_required = [['openai'],['serpapi']]

    def __init__(self, api_keys, main_loop_function):
        super().__init__(api_keys, main_loop_function)

    def execute(self, params, dependent_task_outputs, objective):
        # Your function goes here

        
        # Modify the query based on the dependent task output
        if dependent_task_outputs != "":
            dependent_task = f"Use the dependent task output below as reference to help craft the correct search query for the provided task above. Dependent task output:{dependent_task_outputs}."
        else:
            dependent_task = "."
        query = self.text_completion_tool("You are an AI assistant tasked with generating a Google search query based on the following task: "+params+". If the task looks like a search query, return the identical search query as your response. " + dependent_task + "\nSearch Query:")
        print("\033[90m\033[3m"+"Search query: " +str(query)+"\033[0m")
        # Set the search parameters
        search_params = {
            "engine": "google",
            "q": query,
            "api_key": self.serpapi_api_key,
            "num": 3
        }
        # Perform the web search
        search_results = GoogleSearch(search_params).get_dict()
        
        # Simplify the search results
        search_results = self.simplify_search_results(search_results.get('organic_results', []))
        print("\033[90m\033[3mCompleted search. Now scraping results.\n\033[0m")

        # Store the results from web scraping
        results = ""
        for result in search_results:
            url = result.get('link')
            print("\033[90m\033[3m" + "Scraping: "+url+"" + "...\033[0m")
            content = self.web_scrape_tool({"url": url, "task": params,"objective":objective})
            results += "URL:"+url+"CONTENT:"+str(content) + ". "
        print("\033[90m\033[3m"+str(results[0:100])[0:100]+"...\033[0m")
        # Process the results and generate a report
        results = self.text_completion_tool(f"You are an expert analyst combining the results of multiple web scrapes. Rewrite the following information as one cohesive report without removing any facts, variables, or code snippets. Any chance you get, make sure to capture working or good example code examples. Ignore any reports of not having info, unless all reports say so - in which case explain that the search did not work and suggest other web search queries to try. \n###INFORMATION:{results}.\n###REPORT:")
        return results

    def simplify_search_results(self, search_results):
        simplified_results = []
        for result in search_results:
            simplified_result = {
                "position": result.get("position"),
                "title": result.get("title"),
                "link": result.get("link"),
                "snippet": result.get("snippet")
            }
            simplified_results.append(simplified_result)
        return simplified_results

  
    def text_completion_tool(self, prompt: str):
        messages = [
            {"role": "user", "content": prompt}
        ]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=messages,
            temperature=0.2,
            max_tokens=1500,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
    
        return response.choices[0].message['content'].strip()


    def web_scrape_tool(self, params):
        content = self.fetch_url_content(params['url'])
        if content is None:
            return None
    
        text = self.extract_text(content)
        print("\033[90m\033[3m"+"Scrape completed. Length:" +str(len(text))+".Now extracting relevant info..."+"...\033[0m")
        info = self.extract_relevant_info(params['objective'], text[0:11000], params['task'])
        links = self.extract_links(content)
        #result = f"{info} URLs: {', '.join(links)}"
        result = info
        
        return result
    
    def fetch_url_content(self,url: str):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            print(f"Error while fetching the URL: {e}")
            return ""
    
    def extract_links(self,content: str):
        soup = BeautifulSoup(content, "html.parser")
        links = [link.get('href') for link in soup.findAll('a', attrs={'href': re.compile("^https?://")})]
        return links
    
    def extract_text(self,content: str):
        soup = BeautifulSoup(content, "html.parser")
        text = soup.get_text(strip=True)
        return text
    
    def extract_relevant_info(self, objective, large_string, task):
        chunk_size = 12000
        overlap = 500
        notes = ""
      
        if len(large_string) == 0:
          print("error scraping")
          return "Error scraping."
        
        for i in range(0, len(large_string), chunk_size - overlap):
            
            print("\033[90m\033[3m"+"Reading chunk..."+"\033[0m")  
            chunk = large_string[i:i + chunk_size]
            
            messages = [
                {"role": "system", "content": f"You are an AI assistant."},
                {"role": "user", "content": f"You are an expert AI research assistant tasked with creating or updating the current notes. If the current note is empty, start a current-notes section by exracting relevant data to the task and objective from the chunk of text to analyze. Any chance you get, make sure to capture working or good example code examples. If there is a current note, add new relevant info frol the chunk of text to analyze. Make sure the new or combined notes is comprehensive and well written. Here's the current chunk of text to analyze: {chunk}. ### Here is the current task: {task}.### For context, here is the objective: {objective}.### Here is the data we've extraced so far that you need to update: {notes}.### new-or-updated-note:"}
            ]
    
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-16k-0613",
                messages=messages,
                max_tokens=1500,
                n=1,
                stop="###",
                temperature=0.7,
            )
    
            notes += response.choices[0].message['content'].strip()+". ";
        
        return notes