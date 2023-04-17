from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from duckduckgo_search import ddg
from agents.scrapper_agent import ScrapperAgent


class BrowserAgent:
    def __init__(self, api_key, engine_id):
        self.api_key = api_key
        self.service = build('customsearch', 'v1', developerKey=api_key)
        self.fallback_service = ddg
        self.engine_id = engine_id

     
    def strip_query(self, query):
        if isinstance(query, str):
            return query.replace('\\', ' ')
        elif isinstance(query, tuple):
            old_value, *rest = query
            return old_value.replace('\\', ' ')
    

    def browse_google(self, query, num_results=3):
        try:
            stripped_query = self.strip_query(query)
            res = self.service.cse().list(q=stripped_query, cx=self.engine_id, num=num_results).execute()
            links = [r['link'] for r in res['items']]
            return links[:2]
        
        except HttpError as error:
            print(f'An error occurred while browsing Google: {error}')
            return []


    def browse_ddg(self, query):
        try:
            stripped_query = self.strip_query(query)
            data = self.fallback_service(stripped_query)
            links = [r['href'] for r in data]
            return links[:2]
        
        except Exception as e:
            print(f'An error occurred while browsing DuckDuckGo: {e}')
            return []
        

    def browse(self, query, num_results=3):
        try:
            return self.browse_google(query, num_results)
        
        except HttpError as error:
            print(f'An error occurred while browsing Google: {error}')
            print('Fallback to DuckDuckGo')
            return self.browse_ddg(query)


    def scrape(self, link):
        scrapper = ScrapperAgent(link)
        return scrapper.scrape()


    def search(self, query):
        results = self.browse(query)
        scraped_data = []
        for result in results:
            link = result
            data = self.scrape(link)
            scraped_data.append(data)
        
        return scraped_data
    
    def searchDDG(self, query):
        results = self.browse_ddg(query)
        scraped_data = []
        for result in results:
            link = result
            data = self.scrape(link)
            scraped_data.append(data)
        
        return scraped_data