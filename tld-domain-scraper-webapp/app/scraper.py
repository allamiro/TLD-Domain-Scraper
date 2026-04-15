from __future__ import annotations

import logging
import random
import time
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
    WebDriverException,
)

from app.models import Domain, db

log = logging.getLogger(__name__)

EXCLUDED_PATTERNS = [".gov.ir", "translate.google.com", "google.com/search"]
MAX_PAGES = 10  # per TLD — keep reasonable for a web request context


def _create_driver() -> webdriver.Chrome:
    """Return a headless Chromium WebDriver suitable for running inside Docker."""
    options = Options()
    # Use the system Chromium installed via apt (works on amd64 and arm64)
    options.binary_location = "/usr/bin/chromium"
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    service = Service(executable_path="/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)


def _get_base_domain(url: str) -> str | None:
    """Return scheme://netloc, or None if the URL is malformed."""
    try:
        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        pass
    return None


def _tld_matches(href: str, tld: str) -> bool:
    """
    True only when the URL hostname ends with the given TLD suffix.
    Prevents false positives like '.ir' matching inside '.ireland'.
    """
    try:
        host = urlparse(href).netloc.lower().rstrip(".")
        suffix = tld.lower().lstrip(".")
        return host == suffix or host.endswith("." + suffix)
    except Exception:
        return False


def _is_excluded(href: str) -> bool:
    return any(pat in href for pat in EXCLUDED_PATTERNS)


def _get_next_button(driver: webdriver.Chrome):
    try:
        return driver.find_element(
            By.XPATH, "//a[@id='pnnext' or contains(text(),'Next')]"
        )
    except NoSuchElementException:
        return None


def run_scraper(tlds: list[str]) -> int:
    """
    Scrape Google for each TLD, persist unique base domains to the database,
    and return the total number of new domains inserted.
    """
    driver = _create_driver()
    total_inserted = 0

    try:
        for tld in tlds:
            tld = tld.strip()
            if not tld:
                continue

            log.info(f"Scraping TLD: {tld}")
            found_domains: set[str] = set()

            query = f"site:{tld} -site:.gov.ir"
            driver.get(f"https://www.google.com/search?q={query}")
            time.sleep(2)

            for page in range(MAX_PAGES):
                links = driver.find_elements(By.CSS_SELECTOR, "a")
                log.debug(f"  Page {page + 1}: {len(links)} links")

                for link in links:
                    href = link.get_attribute("href")
                    if not href or _is_excluded(href):
                        continue
                    if _tld_matches(href, tld):
                        base = _get_base_domain(href)
                        if base:
                            found_domains.add(base)

                next_btn = _get_next_button(driver)
                if next_btn:
                    try:
                        # Scroll into view then click via JS to avoid
                        # ElementNotInteractableException in headless mode
                        driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                        driver.execute_script("arguments[0].click();", next_btn)
                        time.sleep(random.uniform(3, 5))
                    except ElementNotInteractableException:
                        log.info(f"  Next button not interactable on page {page + 1}, stopping.")
                        break
                else:
                    break

            log.info(f"  Found {len(found_domains)} unique domains for {tld}")

            # Persist — skip duplicates that are already in the DB
            existing_urls = {
                row.url
                for row in Domain.query.filter_by(tld=tld).with_entities(Domain.url).all()
            }

            new_domains = [d for d in found_domains if d not in existing_urls]
            for url in new_domains:
                db.session.add(Domain(url=url, tld=tld))

            db.session.commit()
            total_inserted += len(new_domains)
            log.info(f"  Inserted {len(new_domains)} new records for {tld}")

    except WebDriverException as e:
        log.error(f"WebDriver error during scraping: {e}")
        db.session.rollback()
        raise
    finally:
        driver.quit()

    return total_inserted
