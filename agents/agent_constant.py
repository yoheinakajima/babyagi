
AVAILABLE_AGENTS = [
    {
      "api_name": "google-place",
      "description": "Find nearby places, using google place api",
      "request_format": "api_name(https://maps.googleapis.com/maps/api/place/{endpoint}, params?)"
    },
    {
      "api_name": "jsonplaceholder",
      "description": "A fake API for testing and prototyping",
      "request_format": "api_name(endpoint, params)"
    },
    {
      "api_name": "openweather",
      "description": "Get weather data",
      "request_format": "api_name(endpoint, params)"
    },
  ]


PROMPT = f"""You are an API provider agent.
Please provide a maximum of 3 requests in a list using any of the following APIs and note that you should be using the following syntax (do not return [description] in output, but take it into account):

1. browse(prompt) [searching the web. provide a prompt for google search engine and no url]
2. openai(prompt) [using GPT3. provide a prompt]
3. yelp(https://api.yelp.com/v3/path, params) [provide only the path, and the params]
4. arxiv(params) [using arxiv API, provide only the params]
5. transformerxl(prompt) [using transformerXL. provide a prompt]
6. wikipedia(params) [provide only the params]
7. pubmed(query) [using the pubmed api, just provide the query]
8. bert(prompt) [classify text using the BERT model]
9. chart(prompt) [Generate charts from data using google/chart transformer]

Our global objective is to write an article on Autoimmune diseases.
Your current task is to Research and write about the different types of autoimmune diseases, including their causes, symptoms, and treatments.
For each request you choose, please use any relevant path/query/prompt and parameter format to Research and write about the different types of autoimmune diseases, including their causes, symptoms, and treatments.
You may include any additional parameters you think would be useful for this task. When using APIs that require parameters, please format them as an object.
Please DO NOT INCLUDE any api keys params anywhere. You should try to set output limits when possible (max 10 results).

Please note that you must use only the listed APIs to generate the requests, and only return the 3 requests you find the most relevant to the task.
Return ONLY the requests as a LIST containing ONLY the API requests without ANY comments, explanations or additional information, this is important."""


# 6. wikipedia(params) [provide only the params]
#             7. pubmed(query) [using the pubmed api, just provide the query]
#             8. clinicaltrials(params) [using the clinicaltrials api, just provide the params]
#             9. newsapi(query) [just provide the query]
#             10. chart(prompt) [Generate charts from data using google/chart transformer]
# 3. yelp(https://api.yelp.com/v3/path, params) [provide only the path, and the params]
#             4. arxiv(params) [using arxiv API, provide only the params]
# 3. openweather(path, params) [provide th path and params]