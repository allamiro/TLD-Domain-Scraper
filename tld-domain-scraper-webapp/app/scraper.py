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
from app.engines import SearchEngine, get_engines, DEFAULT_ENGINES

log = logging.getLogger(__name__)

# Hard cap — still applies per engine per TLD
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


def _is_excluded(href: str, engine: SearchEngine) -> bool:
    """Exclude engine-specific noise URLs and always-excluded patterns."""
    always_excluded = [".gov.ir"]
    patterns = always_excluded + engine.excluded_in_results
    return any(pat in href for pat in patterns)


def _get_next_button(driver: webdriver.Chrome, engine: SearchEngine):
    try:
        return driver.find_element(By.XPATH, engine.next_xpath)
    except NoSuchElementException:
        return None


def _emit(job_id: str | None, message: str) -> None:
    log.info(message)
    if job_id:
        job_store.append_log(job_id, message)


def _scrape_engine(
    driver: webdriver.Chrome,
    engine: SearchEngine,
    tld: str,
    job_id: str | None,
) -> set[str]:
    """
    Run one search engine for one TLD.
    Returns the set of unique base domains found.
    """
    found: set[str] = set()
    url = engine.search_url.format(tld=tld)

    _emit(job_id, f"  [{tld}] [{engine.display_name}] Starting — {url}")
    driver.get(url)
    time.sleep(random.uniform(2, 3))

    page_limit = min(engine.max_pages, MAX_PAGES)

    for page in range(page_limit):
        if job_id:
            job_store.update_job(job_id, current_page=page + 1, current_engine=engine.display_name)

        links = driver.find_elements(By.CSS_SELECTOR, "a")
        page_new: set[str] = set()

        for link in links:
            href = link.get_attribute("href")
            if not href or _is_excluded(href, engine):
                continue
            if _tld_matches(href, tld):
                base = _get_base_domain(href)
                if base and base not in found:
                    page_new.add(base)

        found |= page_new
        _emit(
            job_id,
            f"  [{tld}] [{engine.display_name}] Page {page + 1}: "
            f"+{len(page_new)} new (running total: {len(found)})",
        )

        if job_id:
            job_store.update_job(job_id, domains_found=len(found))

        next_btn = _get_next_button(driver, engine)
        if next_btn:
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(random.uniform(3, 5))
            except ElementNotInteractableException:
                _emit(job_id, f"  [{tld}] [{engine.display_name}] Next not interactable — stopping.")
                break
        else:
            _emit(job_id, f"  [{tld}] [{engine.display_name}] No more pages.")
            break

    _emit(job_id, f"  [{tld}] [{engine.display_name}] Done — {len(found)} unique domains.")
    return found


def run_scraper(
    tlds: list[str],
    job_id: str | None = None,
    mode: str = "append",
    engine_keys: list[str] | None = None,
) -> int:
    """
    Scrape one or more search engines for each TLD and persist unique base domains.

    mode="append"  — keep previously found domains; only insert new ones.
    mode="replace" — delete all existing domains for the TLD first, then re-insert.

    engine_keys — list of engine keys to use (default: google + bing).
    Returns total new domains inserted across all TLDs.
    """
    engines = get_engines(engine_keys or DEFAULT_ENGINES)
    if not engines:
        raise ValueError("No valid engines specified.")

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
                    current_engine=None,
                )

            engine_names = ", ".join(e.display_name for e in engines)
            _emit(job_id, f"TLD {idx + 1}/{len(tlds)}: {tld}  [mode={mode}] [engines: {engine_names}]")

            # Create a ScrapeRun record for this TLD
            scrape_run = ScrapeRun(
                job_id=job_id or "cli",
                tld=tld,
                mode=mode,
                engines=",".join(e.key for e in engines),
                started_at=datetime.now(timezone.utc),
            )
            db.session.add(scrape_run)
            db.session.flush()

            # Replace mode: delete existing rows first
            deleted = 0
            if mode == "replace":
                deleted = Domain.query.filter_by(tld=tld).delete()
                db.session.flush()
                _emit(job_id, f"  [{tld}] Replace: removed {deleted} old domain(s).")

            # --- Scrape all selected engines, aggregate into one set ---
            all_found: set[str] = set()
            for engine in engines:
                try:
                    engine_found = _scrape_engine(driver, engine, tld, job_id)
                    new_from_engine = engine_found - all_found
                    all_found |= engine_found
                    _emit(
                        job_id,
                        f"  [{tld}] [{engine.display_name}] contributed "
                        f"{len(new_from_engine)} unique domain(s) "
                        f"(cross-engine total: {len(all_found)})",
                    )
                    if job_id:
                        job_store.update_job(job_id, domains_found=len(all_found))
                except WebDriverException as e:
                    msg = e.msg if hasattr(e, "msg") else str(e)
                    _emit(job_id, f"  [{tld}] [{engine.display_name}] ERROR: {msg} — skipping engine.")
                    # Don't abort the whole job; continue with next engine

            _emit(job_id, f"  [{tld}] All engines done. {len(all_found)} unique domain(s) total.")

            # --- Persist ---
            if mode == "append":
                existing_urls = {
                    row.url
                    for row in Domain.query.filter_by(tld=tld)
                                           .with_entities(Domain.url).all()
                }
                new_domains = [d for d in all_found if d not in existing_urls]
            else:
                new_domains = list(all_found)

            for url in new_domains:
                db.session.add(Domain(url=url, tld=tld, run_id=scrape_run.id))

            scrape_run.finished_at = datetime.now(timezone.utc)
            scrape_run.domains_found = len(all_found)
            scrape_run.domains_inserted = len(new_domains)
            scrape_run.domains_deleted = deleted

            db.session.commit()
            total_inserted += len(new_domains)
            _emit(
                job_id,
                f"  [{tld}] Saved {len(new_domains)} new domain(s)."
                + (f" ({deleted} removed)" if deleted else ""),
            )

            if job_id:
                job_store.update_job(job_id, domains_inserted=total_inserted)

    except WebDriverException as e:
        msg = e.msg if hasattr(e, "msg") else str(e)
        _emit(job_id, f"FATAL ERROR: {msg}")
        db.session.rollback()
        raise
    finally:
        driver.quit()
        _emit(job_id, "Browser closed.")

    return total_inserted
