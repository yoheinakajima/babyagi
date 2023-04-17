import json
from bs4 import BeautifulSoup
import requests

from Bio import Entrez

class APIFactory:
    def __init__(self, api_key):
        self.api_key = api_key
    
    def make_api_call(self, endpoint, params):
        raise NotImplementedError

class YelpFusionAPI(APIFactory):
    def make_api_call(self, endpoint, params):
        print(endpoint, params)
        base_url = "https://api.yelp.com/v3"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        params_json = json.loads(params)
        path = endpoint.strip('"')
        response = requests.get(f"{base_url}{path}", headers=headers, params=params_json)
        print(response.url)
        if response.status_code >= 400:
            print(f"Error {response.status_code}: {response.content}")
            return None
        return response.json()

class OpenWeatherAPI(APIFactory):
    def make_api_call(self, endpoint, params):
        base_url = "https://api.openweathermap.org/data/2.5"
        params["appid"] = self.api_key
        response = requests.get(f"{base_url}/{endpoint}", params=params)
        return response.json()

class RandomUserAPI(APIFactory):
    def make_api_call(self, endpoint, params):
        base_url = "https://randomuser.me/api"
        response = requests.get(f"{base_url}/{endpoint}", params=params)
        return response.json()

class JSONPlaceholderAPI(APIFactory):
    def make_api_call(self, endpoint, params):
        base_url = "https://jsonplaceholder.typicode.com"
        response = requests.get(f"{base_url}/{endpoint}", params=params)
        return response.json()
    
class NHANESApi(APIFactory):        
    def make_api_call(self, endpoint, params):
        # Convert the parameters to a dictionary
        # params_dict = dict(params)
        
        # # Use the NHANES library to retrieve the data
        # data = load_NHANES_data(endpoint, params_dict)
        
        # # Convert the data to JSON format and return it
        # return data.to_json(orient="records")
        return
        
class ArxivAPI:
    def __init__(self):
        self.base_url = 'https://export.arxiv.org/api/query'
        
    def make_api_call(self, params):
        response = requests.get(self.base_url, params=params)
        soup = BeautifulSoup(response.text, 'xml')
        entries = soup.find_all('entry')
        abstracts = []
        for entry in entries:
            summary = entry.summary.text
            abstracts.append(summary)
        
        return abstracts
    
class NewsApi:
    def __init__(self):
        self.base_url = "https://newsapi.org/v2/"
        
    def get_top_headlines(self, country=None, category=None):
        url = self.base_url + "top-headlines"
        params = {
            "apiKey": self.api_key
        }
        if country:
            params["country"] = country
        if category:
            params["category"] = category
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()["articles"]
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return []
        
    def make_api_call(self, query, language=None, sources=None):
        url = self.base_url + "everything"
        params = {
            "apiKey": self.api_key,
            "q": query
        }
        if language:
            params["language"] = language
        if sources:
            params["sources"] = sources
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()["articles"]
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return []
        
class WikipediaAPI:
    def make_api_call(self, params_str):
        print(params_str)
        base_url = "https://en.wikipedia.org/w/api.php"
        params = json.loads(params_str)
        params["format"] = "json"
        params["action"] = "query"
        params["prop"] = "extracts"
        params["exintro"] = ""
        params["explaintext"] = ""
        params["redirects"] = 1
        params["formatversion"] = 2
        params["utf8"] = 1
        params["generator"] = "search"
        params["gsrlimit"] = 1
        params["gsrwhat"] = "text"
        params["gsrinfo"] = ""
        params["gsrprop"] = "snippet"
        params["gsrsearch"] = params["srsearch"]

        headers = {
            "User-Agent": "My Wikipedia API Client/1.0"
        }

        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()

        data = response.json()
        if "error" in data:
            raise ValueError(f"Wikipedia API Error: {data['error']['info']}")

        pages = data["query"]["pages"]
        if len(pages) == 0:
            return None

        page = pages[0]
        title = page["title"]
        extract = page["extract"]
        return {"title": title, "extract": extract}

class PubMedAPI:
    def __init__(self):
        self.email = self.api_key
        Entrez.email = self.api_key

    def make_api_call(self, query):
        handle = Entrez.esearch(db="pubmed", term=query, retmax=1)
        record = Entrez.read(handle)
        handle.close()

        if int(record["Count"]) == 0:
            return None

        id_list = record["IdList"]
        handle = Entrez.efetch(db="pubmed", id=id_list, rettype="medline", retmode="text")
        record = handle.read()
        handle.close()

        return record
    
class ClinicalTrialsAPI:
    def make_api_call(self, params):
        base_url = "https://clinicaltrials.gov/api/query/study_fields?"
        response = requests.get(base_url, params=params)
        return response.json()