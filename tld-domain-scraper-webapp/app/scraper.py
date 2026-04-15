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
from app import jobs as job_store

log = logging.getLogger(__name__)

EXCLUDED_PATTERNS = [".gov.ir", "translate.google.com", "google.com/search"]
MAX_PAGES = 10


def _create_driver() -> webdriver.Chrome:
    options = Options()
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
    try:
        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        pass
    return None


def _tld_matches(href: str, tld: str) -> bool:
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


def _emit(job_id: str | None, message: str) -> None:
    """Log to both Python logger and the job progress store."""
    log.info(message)
    if job_id:
        job_store.append_log(job_id, message)


def run_scraper(tlds: list[str], job_id: str | None = None) -> int:
    """
    Scrape Google for each TLD and persist unique base domains.
    If job_id is provided, progress is written to the job store so the
    browser can poll it in real time.
    Returns the total number of new domains inserted.
    """
    driver = _create_driver()
    total_inserted = 0

    try:
        for idx, tld in enumerate(tlds):
            tld = tld.strip()
            if not tld:
                continue

            if job_id:
                job_store.update_job(
                    job_id,
                    tld_index=idx,
                    current_tld=tld,
                    current_page=0,
                )

            _emit(job_id, f"Starting TLD {idx + 1}/{len(tlds)}: {tld}")
            found_domains: set[str] = set()

            query = f"site:{tld} -site:.gov.ir"
            driver.get(f"https://www.google.com/search?q={query}")
            time.sleep(2)

            for page in range(MAX_PAGES):
                if job_id:
                    job_store.update_job(job_id, current_page=page + 1)

                links = driver.find_elements(By.CSS_SELECTOR, "a")
                page_domains: set[str] = set()

                for link in links:
                    href = link.get_attribute("href")
                    if not href or _is_excluded(href):
                        continue
                    if _tld_matches(href, tld):
                        base = _get_base_domain(href)
                        if base:
                            page_domains.add(base)

                found_domains |= page_domains
                _emit(
                    job_id,
                    f"  [{tld}] Page {page + 1}: {len(page_domains)} new domains "
                    f"(running total: {len(found_domains)})",
                )

                if job_id:
                    job_store.update_job(job_id, domains_found=len(found_domains))

                next_btn = _get_next_button(driver)
                if next_btn:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                        driver.execute_script("arguments[0].click();", next_btn)
                        time.sleep(random.uniform(3, 5))
                    except ElementNotInteractableException:
                        _emit(job_id, f"  [{tld}] Next button not interactable — stopping pagination.")
                        break
                else:
                    _emit(job_id, f"  [{tld}] No more pages.")
                    break

            _emit(job_id, f"  [{tld}] Collected {len(found_domains)} unique domains.")

            # Deduplicate against existing DB records
            existing_urls = {
                row.url
                for row in Domain.query.filter_by(tld=tld).with_entities(Domain.url).all()
            }
            new_domains = [d for d in found_domains if d not in existing_urls]
            for url in new_domains:
                db.session.add(Domain(url=url, tld=tld))

            db.session.commit()
            total_inserted += len(new_domains)
            _emit(job_id, f"  [{tld}] Saved {len(new_domains)} new record(s) to database.")

            if job_id:
                job_store.update_job(job_id, domains_inserted=total_inserted)

    except WebDriverException as e:
        msg = f"WebDriver error: {e.msg if hasattr(e, 'msg') else str(e)}"
        _emit(job_id, f"ERROR: {msg}")
        db.session.rollback()
        raise
    finally:
        driver.quit()
        _emit(job_id, "Browser closed.")

    return total_inserted
