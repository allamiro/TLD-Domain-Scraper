#!/usr/bin/env python3

import platform
import logging
import os
import re
import time
import random
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, NoSuchElementException

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# --- OS-specific Chrome paths ---
current_os = platform.system()

if current_os == "Darwin":  # macOS
    chrome_driver_path = "/opt/homebrew/bin/chromedriver"
    chrome_binary_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
elif current_os == "Linux":
    chrome_driver_path = "/usr/bin/chromedriver"
    chrome_binary_path = "/usr/bin/google-chrome"
elif current_os == "Windows":
    chrome_driver_path = "C:\\path\\to\\chromedriver.exe"
    chrome_binary_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
else:
    raise RuntimeError(f"Unsupported OS: {current_os}")

# --- Output directory ---
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- TLDs to search ---
tlds = [
    ".IR",
    ".PERSIANBLOG.IR",
    ".RZB.IR",
    ".CO.IR",
    ".AC.IR",
    ".SCH.IR",
    ".ORG.IR",
    ".ID.IR",
    ".R98.IR",
    ".EPAGE.IR",
]

# Domains to always exclude from results
EXCLUDED_PATTERNS = [".gov.ir", "translate.google.com", "google.com/search"]

# Maximum pages to scrape per TLD
MAX_PAGES = 30


def create_driver() -> webdriver.Chrome:
    """Create and return a configured Chrome WebDriver."""
    options = Options()
    options.binary_location = chrome_binary_path
    # Run headless so it works without a display (CI / server environments)
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # Mimic a real browser UA to reduce bot-detection
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    service = Service(executable_path=chrome_driver_path)
    return webdriver.Chrome(service=service, options=options)


def get_base_domain(url: str) -> str | None:
    """Return scheme + netloc for a URL, or None if the URL is malformed."""
    try:
        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        pass
    return None


def tld_matches(href: str, tld: str) -> bool:
    """
    Return True only when the URL's hostname ends with the given TLD.
    Avoids false positives like '.ir' matching inside '.ireland'.
    """
    try:
        host = urlparse(href).netloc.lower().rstrip(".")
        suffix = tld.lower().lstrip(".")
        return host == suffix or host.endswith("." + suffix)
    except Exception:
        return False


def is_excluded(href: str) -> bool:
    return any(pat in href for pat in EXCLUDED_PATTERNS)


def is_captcha_present(driver: webdriver.Chrome) -> bool:
    try:
        el = driver.find_element(
            By.XPATH,
            "//div[@id='captcha'] | //iframe[contains(@src,'recaptcha')] | //div[@id='recaptcha']",
        )
        return el is not None
    except NoSuchElementException:
        return False


def get_next_button(driver: webdriver.Chrome):
    try:
        return driver.find_element(
            By.XPATH, "//a[@id='pnnext' or contains(text(),'Next')]"
        )
    except NoSuchElementException:
        return None


def tld_to_filename(tld: str) -> str:
    """Convert a TLD like '.PERSIANBLOG.IR' to a safe filename stem like 'persianblog_ir'."""
    parts = [p for p in tld.lower().split(".") if p]
    return "_".join(parts)


def scrape_tld(driver: webdriver.Chrome, tld: str) -> set:
    """Scrape all result pages for one TLD and return a set of unique base domains."""
    log.info(f"Starting scrape for TLD: {tld}")
    domain_set: set[str] = set()

    query = f"site:{tld} -site:.gov.ir"
    url = f"https://www.google.com/search?q={query}"
    driver.get(url)
    time.sleep(2)

    for page in range(MAX_PAGES):
        if is_captcha_present(driver):
            log.warning("CAPTCHA detected — please solve it in the browser window.")
            input("Press Enter after solving the CAPTCHA to continue...")
            log.info("Resuming after CAPTCHA.")

        links = driver.find_elements(By.CSS_SELECTOR, "a")
        log.info(f"  Page {page + 1}: found {len(links)} links")

        for link in links:
            href = link.get_attribute("href")
            if not href:
                continue
            if is_excluded(href):
                continue
            if tld_matches(href, tld):
                base = get_base_domain(href)
                if base:
                    domain_set.add(base)

        next_btn = get_next_button(driver)
        if next_btn:
            next_btn.click()
            time.sleep(random.uniform(3, 5))
        else:
            log.info(f"  No more pages for {tld} (stopped at page {page + 1})")
            break

    log.info(f"Collected {len(domain_set)} unique domains for {tld}")
    return domain_set


def save_results(tld: str, domains: set) -> str:
    """Write sorted domains to a file and return the path."""
    stem = tld_to_filename(tld)
    filename = os.path.join(OUTPUT_DIR, f"iran_{stem}.txt")
    with open(filename, "w") as f:
        for domain in sorted(domains):
            f.write(domain + "\n")
    return filename


def main():
    all_domains: dict[str, set] = {}
    driver = create_driver()

    try:
        for tld in tlds:
            domains = scrape_tld(driver, tld)
            all_domains[tld] = domains

            filepath = save_results(tld, domains)
            log.info(f"Saved {len(domains)} domains for {tld} → {filepath}")

    except WebDriverException as e:
        log.error(f"WebDriver error: {e}")
    finally:
        driver.quit()
        log.info("Browser closed.")

    # Write a combined summary file
    summary_path = os.path.join(OUTPUT_DIR, "all_domains.txt")
    with open(summary_path, "w") as f:
        for tld, domains in all_domains.items():
            for domain in sorted(domains):
                f.write(f"{domain}\t{tld}\n")
    log.info(f"Combined summary written to {summary_path}")

    total = sum(len(v) for v in all_domains.values())
    log.info(f"Done. Total unique domains collected: {total}")


if __name__ == "__main__":
    main()
