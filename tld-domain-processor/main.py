# main.py
import os
import requests
from urllib.parse import urlparse
from site_processors import get_processor

def read_domains(file_path):
    with open(file_path, 'r') as f:
        domains = [line.strip() for line in f if line.strip()]
    return domains

def save_article(domain, title, content):
    directory = os.path.join('output', domain)
    os.makedirs(directory, exist_ok=True)
    file_name = f"{title[:50]}.txt".replace('/', '_')  # Sanitize filename
    file_path = os.path.join(directory, file_name)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"{title}\n\n{content}")

def process_domain(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    processor = get_processor(domain)
    if processor:
        print(f"Processing {url} with {processor.__name__}")
        title, content = processor(url)
        save_article(domain, title, content)
    else:
        print(f"No processor found for {domain}, using generic processor.")
        from site_processors.generic_processor import process
        title, content = process(url)
        save_article(domain, title, content)

if __name__ == "__main__":
    domains = read_domains('domains.txt')
    for url in domains:
        process_domain(url)
