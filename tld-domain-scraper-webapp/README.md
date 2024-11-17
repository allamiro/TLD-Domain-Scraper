## TLD Domain Scraper Web App
### Overview

The TLD Domain Scraper Web App is a Python-based application built with Flask to scrape and manage domain names across various Top-Level Domains (TLDs). The app allows users to:

* Scrape domain names using search queries.
* Store and manage scraped domains in a PostgreSQL database.
* View, filter, and download the results through a responsive web interface.

## Technology Stack
* Backend: Flask
* Frontend: HTML, CSS, JavaScript (with Bootstrap for styling)
* Database: PostgreSQL
* Scraper: Selenium
* Containerization: Docker and Docker Compose (optional)

1. Prerequisites
Ensure you have the following installed:

Python (3.8+)
PostgreSQL
Docker and Docker Compose (optional)


2. Run the App
Start the Flask development server:


```python run.py
Open your browser and navigate to http://localhost:5000.
```

3. Using Docker Compose

Build and start the app with Docker Compose:

```docker-compose up --build```
Access the app at ```http://localhost:5000```.

