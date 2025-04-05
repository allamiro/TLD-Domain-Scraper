# site_processors/example_com_processor.py
import requests
from bs4 import BeautifulSoup

def process(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Custom extraction logic for example.com
    title = soup.find('h1', class_='article-title').get_text(strip=True)
    content_div = soup.find('div', class_='article-content')
    content = content_div.get_text(separator='\n').strip()

    return title, content
