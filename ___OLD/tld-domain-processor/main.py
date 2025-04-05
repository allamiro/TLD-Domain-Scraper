# main.py
import os
import logging
from urllib.parse import urlparse
from site_processors import get_processor

# Configure logging to output errors to a file
logging.basicConfig(
    filename='error.log',
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s %(message)s'
)

def read_domains(file_path):
    try:
        with open(file_path, 'r') as f:
            domains = [line.strip() for line in f if line.strip()]
        return domains
    except FileNotFoundError as e:
        logging.error(f"Domains file not found: {e}")
        print(f"Error: Domains file not found at '{file_path}'.")
        return []

def sanitize_filename(filename):
    # Remove or replace characters that are invalid in file names
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def save_article(domain, title, content):
    try:
        directory = os.path.join('output', domain)
        os.makedirs(directory, exist_ok=True)
        sanitized_title = sanitize_filename(title[:50]) or 'untitled'
        file_name = f"{sanitized_title}.txt"
        file_path = os.path.join(directory, file_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"{title}\n\n{content}")
    except Exception as e:
        logging.error(f"Failed to save article for domain '{domain}': {e}")
        print(f"Failed to save article '{title}' for domain '{domain}': {e}")

def process_domain(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc or parsed_url.path  # Handle URLs without scheme
    processor = get_processor(domain)
    try:
        if processor:
            print(f"Processing {url} with {processor.__name__}")
            title, content = processor(url)
        else:
            print(f"No processor found for {domain}, using generic processor.")
            from site_processors.generic_processor import process
            title, content = process(url)

        if title and content:
            save_article(domain, title, content)
        else:
            error_msg = f"No content extracted from {url}."
            logging.error(error_msg)
            print(error_msg)
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error when processing {url}: {e}"
        logging.error(error_msg)
        print(error_msg)
    except Exception as e:
        error_msg = f"Failed to process {url}: {e}"
        logging.error(error_msg)
        print(error_msg)

if __name__ == "__main__":
    domains = read_domains('domains.txt')
    if not domains:
        print("No domains to process.")
    else:
        for url in domains:
            process_domain(url)
