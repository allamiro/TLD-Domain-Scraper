import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from urllib.parse import urlparse
import time
import random
from typing import List, Set
import logging

logger = logging.getLogger(__name__)

class DomainScraper:
    def __init__(self):
        self.current_os = platform.system()
        self._setup_chrome_driver()
        
    def _setup_chrome_driver(self):
        """Setup Chrome driver based on operating system"""
        if self.current_os == "Darwin":  # macOS
            chrome_driver_path = "/opt/homebrew/bin/chromedriver"
            chrome_binary_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        elif self.current_os == "Linux":
            chrome_driver_path = "/usr/bin/chromedriver"
            chrome_binary_path = "/usr/bin/google-chrome"
        elif self.current_os == "Windows":
            chrome_driver_path = "C:\\path\\to\\chromedriver.exe"
            chrome_binary_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        else:
            raise Exception(f"Unsupported OS: {self.current_os}")

        chrome_options = Options()
        chrome_options.binary_location = chrome_binary_path
        chrome_options.add_argument('--headless')  # Run in headless mode
        service = Service(executable_path=chrome_driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def get_base_domain(self, url: str) -> str:
        """Extract base domain from URL"""
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}"

    def is_captcha_present(self) -> bool:
        """Detect if CAPTCHA is present on the page"""
        try:
            captcha_element = self.driver.find_element(By.XPATH, "//div[@id='captcha'] | //iframe[contains(@src, 'recaptcha')]")
            return True if captcha_element else False
        except:
            return False

    def is_next_button_present(self):
        """Check for presence of 'Next' button"""
        try:
            next_button = self.driver.find_element(By.XPATH, "//a[@id='pnnext' or contains(text(), 'Next')]")
            return next_button
        except:
            return None

    async def scrape_tld(self, tld: str) -> Set[str]:
        """Scrape domains for a specific TLD"""
        logger.info(f"Starting scraping for TLD: {tld}")
        domain_list = set()
        base_query = "-site:.gov.ir"
        query = f"site:{tld} {base_query}"
        url = f"https://www.google.com/search?q={query}"

        try:
            self.driver.get(url)
            time.sleep(2)  # Allow page to load

            for page in range(30):  # Limit to 30 pages
                if self.is_captcha_present():
                    logger.warning("CAPTCHA detected! Skipping remaining pages.")
                    break

                results = self.driver.find_elements(By.CSS_SELECTOR, 'a')
                logger.info(f"Processing page {page + 1}")

                for link in results:
                    href = link.get_attribute('href')
                    if href and tld.lower() in href.lower() and '.gov.ir' not in href and 'translate.google.com' not in href:
                        base_domain = self.get_base_domain(href)
                        domain_list.add(base_domain)

                next_button = self.is_next_button_present()
                if next_button:
                    next_button.click()
                    time.sleep(random.uniform(3, 5))
                else:
                    break

        except Exception as e:
            logger.error(f"Error scraping TLD {tld}: {str(e)}")
        finally:
            self.driver.quit()

        return domain_list

    def __del__(self):
        """Cleanup: close the browser"""
        try:
            self.driver.quit()
        except:
            pass 