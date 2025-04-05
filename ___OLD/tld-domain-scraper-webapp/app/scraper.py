import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime
from app.models import Domain, db

def run_scraper(tlds):
    # Initialize WebDriver (ensure chromedriver is installed)
    driver = webdriver.Chrome()

    base_query = "-site:.gov"  # Exclude government sites
    scraped_domains = []

    for tld in tlds:
        query = f"site:{tld} {base_query}"
        driver.get(f"https://www.google.com/search?q={query}")
        links = driver.find_elements(By.CSS_SELECTOR, "a")

        for link in links:
            href = link.get_attribute("href")
            if href and tld.lower() in href.lower() and '.gov' not in href:
                scraped_domains.append(href)

    driver.quit()

    # Store in PostgreSQL
    for domain in scraped_domains:
        new_domain = Domain(
            url=domain,
            tld=tld,
            timestamp=datetime.utcnow()
        )
        db.session.add(new_domain)

    db.session.commit()
    return len(scraped_domains)  # Return count of scraped domains
