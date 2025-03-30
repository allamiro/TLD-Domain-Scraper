# TLD Domain Scraper Web Application

A FastAPI-based web application for scraping and analyzing domain names across multiple country-level Top-Level Domains (TLDs).

## Features

- Web interface for triggering domain scraping
- REST API endpoints for domain management
- SQLite database for storing scraped domains
- Modern UI with Tailwind CSS and HTMX
- Asynchronous domain scraping with Selenium

## Prerequisites

- Python 3.8+
- Chrome browser installed
- ChromeDriver installed and in PATH

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install ChromeDriver:
- macOS: `brew install chromedriver`
- Linux: `sudo apt install chromium-chromedriver`
- Windows: Download from [ChromeDriver website](https://sites.google.com/chromium.org/driver/)

## Running the Application

1. Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

2. Open your browser and navigate to:
```
http://localhost:8000
```

## API Endpoints

- `GET /`: Web interface for domain scraping
- `POST /scrape`: Trigger domain scraping for a specific TLD
- `GET /domains`: List all stored domains
- `GET /domains/{tld}`: List domains for a specific TLD

## Development

The application structure:
```
scrapper-web-app-dev/
├── app/
│   ├── main.py           # FastAPI application and routes
│   ├── models.py         # Database models
│   ├── services/
│   │   └── scraper.py    # Domain scraping service
│   └── templates/
│       └── index.html    # Web interface template
├── static/              # Static files (CSS, JS)
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 