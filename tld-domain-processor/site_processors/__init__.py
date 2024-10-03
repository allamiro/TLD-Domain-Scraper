# site_processors/__init__.py
from urllib.parse import urlparse
from . import example_com_processor

SITE_PROCESSORS = {
    'example.com': example_com_processor.process,
    # Add more domain-specific processors here
}

def get_processor(domain):
    return SITE_PROCESSORS.get(domain, None)
