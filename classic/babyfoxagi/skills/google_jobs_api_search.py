from skills.skill import Skill
from serpapi import GoogleSearch
import openai
import litellm
from bs4 import BeautifulSoup
import requests
import re
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
}

class GoogleJobsAPISearch(Skill):
    name = 'google_jobs_api_search'
    description = 'A skill for searching for job listings using the Google Jobs API.'
    api_keys_required = [['serpapi']]

    def __init__(self, api_keys, main_loop_function):
        super().__init__(api_keys, main_loop_function)

    def execute(self, params, dependent_task_outputs, objective):
        # Modify the query based on the dependent task output
        if dependent_task_outputs != "":
            dependent_task = f"Use the dependent task output below as reference to help craft the correct search query for the provided task above. Dependent task output:{dependent_task_outputs}."
        else:
            dependent_task = ""

        # Generate the search query
        query = self.text_completion_tool(f"You are an AI assistant tasked with generating a Google Jobs API search query based on the following task: {params}. If the task looks like a search query, return the identical search query as your response. {dependent_task}\nSearch Query:")
        print("\033[90m\033[3m" + "Search query: " + str(query) + "\033[0m")

        # Set the search parameters
        search_params = {
            "engine": "google_jobs",
            "q": query,
            "api_key": self.serpapi_api_key,
            "num": 3
        }

        # Perform the job search
        job_results = GoogleSearch(search_params).get_dict()

        # Simplify the job results
        simplified_results = self.simplify_job_results(job_results.get('jobs_results', []))

        # Generate a report
        report = self.text_completion_tool(f"You are an expert analyst combining the results of multiple job searches. Rewrite the following information as one cohesive report without removing any facts. Keep job URL for each. Ignore any reports of not having info, unless all reports say so - in which case explain that the search did not work and suggest other job search queries to try.\n###INFORMATION:{simplified_results}.\n###REPORT:")

        time.sleep(1)

        return report

    def simplify_job_results(self, job_results):
        simplified_results = []
        for result in job_results:
            simplified_result = {
                "title": result.get("title"),
                "company_name": result.get("company_name"),
                "location": result.get("location"),
                "via": result.get("via"),
                "description": result.get("description"),
                "related_links": result.get("related_links"),
                "extensions": result.get("extensions"),
                "detected_extensions": result.get("detected_extensions")
            }
            simplified_results.append(simplified_result)
        return simplified_results

    def text_completion_tool(self, prompt: str):
        messages = [
            {"role": "user", "content": prompt}
        ]
        response = litellm.completion(
            model="gpt-3.5-turbo-16k",
            messages=messages,
            temperature=0.2,
            max_tokens=500,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        return response.choices[0].message['content'].strip()