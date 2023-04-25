import requests
from bs4 import BeautifulSoup
import re

# Internet search for query, return snippets and links
def search(query, api_key, search_engine_id, num_results, start_index):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": query,
        "num": num_results,
        "start": start_index
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        try:
            json_data = response.json()
            if "items" in json_data:
                return json_data["items"], response.json()["items"]
            else:
                print("No items found in the response.")
                return [], []
        except ValueError as e:
            print(f"Error while parsing JSON data: {e}")
            return [], []
    else:
        print(f"Error: {response.status_code}")
        return [], []


# Get snippets for current page
def search_google(query, api_key, search_engine_id, num_results, start_index):
    results, links = search(query, api_key, search_engine_id, num_results, start_index)
    return [result['snippet'] for result in results], [link['link'] for link in links]


# Collect all snippets (for multiple top pages)
def get_snippets(topic, api_key, search_engine_id, num_results, num_pages):
    all_snippets = []
    links = []
    i = 1
    for page in range(1, num_pages * num_results, num_results):
        snippets, link = search_google(topic, api_key, search_engine_id, num_results, start_index=i)
        all_snippets.extend(snippets)
        links.extend(link)
        i += num_results
    return all_snippets, links


def extract_relevant_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        content_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        content = ' '.join([tag.text for tag in soup.find_all(content_tags)])
        content = re.sub(r'\t', ' ', content)
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\n', ' ', content)
        return content.strip()
    else:
        print(f"Error: {response.status_code}")
        return ""
    

# API: Get top list results and top page content
def get_toplist(topic, api_key, search_engine_id, num_results, num_pages):
    snippets, links = get_snippets(topic, api_key, search_engine_id, num_results, num_pages)
    if links:
        webpage_content = extract_relevant_content(links[0])
    else:
        webpage_content = ""
    #print(f"Topresults: {snippets}\n")
    #print(str(links[0]) + ": " + webpage_content)
    return snippets, webpage_content, links[0]
