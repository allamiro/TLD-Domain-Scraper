# site_processors/generic_processor.py
import requests
from bs4 import BeautifulSoup

def process(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Try to extract the title and content using common tags
    title = soup.title.string if soup.title else 'No Title'

    # Try common article content selectors
    article = soup.find('article')
    if article:
        content = article.get_text(separator='\n').strip()
    else:
        # Fallback: Get all text
        content = soup.get_text(separator='\n').strip()

    return title, content
