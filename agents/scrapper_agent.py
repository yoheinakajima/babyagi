import json
import requests
from bs4 import BeautifulSoup


class ScrapperAgent:
    def __init__(self, url):
        self.url = url
        
    def scrape(self):
        # Send request
        try:
            response = requests.get(self.url, timeout=10)
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract text
            text = soup.get_text()
            
            # Convert text to dictionary
            result_dict = {'text': text}
            json_string = json.dumps(result_dict)
            
            return json_string
        except requests.exceptions.Timeout:
            return 'Request timed out'
        except:
            return 'Error scraping website'