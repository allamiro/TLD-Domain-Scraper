from __future__ import annotations

import logging
import random
import time
from datetime import datetime, timezone
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

from app.models import Domain, ScrapeRun, db
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
    log.info(message)
    if job_id:
        job_store.append_log(job_id, message)


def run_scraper(tlds: list[str], job_id: str | None = None,
                mode: str = "append") -> int:
    """
    Scrape Google for each TLD and persist unique base domains.

    mode="append"  — keep every previously found domain; only insert new ones.
    mode="replace" — delete all existing domains for the TLD first, then insert
                     everything found in this run fresh.

    Returns total new domains inserted across all TLDs.
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

            _emit(job_id, f"Starting TLD {idx + 1}/{len(tlds)}: {tld}  [mode={mode}]")

            # Create a ScrapeRun record for this TLD
            scrape_run = ScrapeRun(
                job_id=job_id or "cli",
                tld=tld,
                mode=mode,
                started_at=datetime.now(timezone.utc),
            )
            db.session.add(scrape_run)
            db.session.flush()  # get the id before we start adding domains

            # --- Replace mode: delete previous domains for this TLD ---
            deleted = 0
            if mode == "replace":
                deleted = Domain.query.filter_by(tld=tld).delete()
                db.session.flush()
                _emit(job_id, f"  [{tld}] Replaced: removed {deleted} old domain(s).")

            # --- Scrape pages ---
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
                    f"  [{tld}] Page {page + 1}: {len(page_domains)} domain(s) "
                    f"(total so far: {len(found_domains)})",
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
                        _emit(job_id, f"  [{tld}] Next button not interactable — stopping.")
                        break
                else:
                    _emit(job_id, f"  [{tld}] No more pages.")
                    break

            _emit(job_id, f"  [{tld}] Scrape done. {len(found_domains)} unique domain(s) collected.")

            # --- Persist ---
            if mode == "append":
                existing_urls = {
                    row.url
                    for row in Domain.query.filter_by(tld=tld)
                                           .with_entities(Domain.url).all()
                }
                new_domains = [d for d in found_domains if d not in existing_urls]
            else:
                # replace mode already deleted old rows
                new_domains = list(found_domains)

            for url in new_domains:
                db.session.add(Domain(url=url, tld=tld, run_id=scrape_run.id))

            # Finalize the ScrapeRun record
            scrape_run.finished_at = datetime.now(timezone.utc)
            scrape_run.domains_found = len(found_domains)
            scrape_run.domains_inserted = len(new_domains)
            scrape_run.domains_deleted = deleted

            db.session.commit()
            total_inserted += len(new_domains)
            _emit(
                job_id,
                f"  [{tld}] Saved {len(new_domains)} new domain(s)."
                + (f" ({deleted} old removed)" if deleted else ""),
            )

            if job_id:
                job_store.update_job(job_id, domains_inserted=total_inserted)

    except WebDriverException as e:
        msg = e.msg if hasattr(e, "msg") else str(e)
        _emit(job_id, f"ERROR: {msg}")
        db.session.rollback()
        raise
    finally:
        driver.quit()
        _emit(job_id, "Browser closed.")

    return total_inserted
