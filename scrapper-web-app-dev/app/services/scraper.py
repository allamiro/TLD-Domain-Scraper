import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from urllib.parse import urlparse
import time
import random
from typing import List, Set, Optional
import logging
from fastapi import WebSocket
import os

logger = logging.getLogger(__name__)

class DomainScraper:
    def __init__(self, websocket: Optional[WebSocket] = None):
        self.current_os = platform.system()
        self.websocket = websocket
        self.is_cancelled = False
        self.driver = None
        self._setup_chrome_driver()
        
    def _setup_chrome_driver(self):
        """Setup Chrome driver based on operating system"""
        if self.current_os == "Darwin":  # macOS
            # Use ChromeDriver from the project directory
            chrome_driver_path = os.path.join(os.path.dirname(__file__), "..", "..", "chromedriver")
            chrome_binary_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            
            # Set ChromeDriver permissions
            os.chmod(chrome_driver_path, 0o755)
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
        
        # Configure window size and position
        chrome_options.add_argument("--window-size=800,600")
        chrome_options.add_argument("--window-position=0,0")  # Position on the left side
        
        # Additional options for better scraping
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Add user agent to avoid detection
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        service = Service(executable_path=chrome_driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    async def send_progress(self, message: str, progress: float = None):
        """Send progress updates through WebSocket"""
        if self.websocket:
            try:
                await self.websocket.send_json({
                    "type": "progress",
                    "message": message,
                    "progress": progress
                })
            except Exception as e:
                logger.error(f"Error sending progress: {str(e)}")

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
            await self.send_progress(f"Starting scraping for {tld}", 0)
            self.driver.get(url)
            time.sleep(3)  # Allow page to load

            for page in range(30):  # Limit to 30 pages
                if self.is_cancelled:
                    await self.send_progress("Scraping cancelled by user", 0)
                    break

                if self.is_captcha_present():
                    await self.send_progress("CAPTCHA detected! Please solve it manually.", 0)
                    # Wait for user to solve CAPTCHA
                    while self.is_captcha_present():
                        if self.is_cancelled:
                            break
                        time.sleep(2)

                if self.is_cancelled:
                    break

                results = self.driver.find_elements(By.CSS_SELECTOR, 'a')
                await self.send_progress(f"Processing page {page + 1}", (page + 1) / 30)

                for link in results:
                    if self.is_cancelled:
                        break
                    href = link.get_attribute('href')
                    if href and tld.lower() in href.lower() and '.gov.ir' not in href and 'translate.google.com' not in href:
                        base_domain = self.get_base_domain(href)
                        domain_list.add(base_domain)
                        await self.send_progress(f"Found domain: {base_domain}", None)

                next_button = self.is_next_button_present()
                if next_button:
                    next_button.click()
                    time.sleep(random.uniform(3, 5))
                else:
                    break

            await self.send_progress(f"Completed scraping for {tld}. Found {len(domain_list)} domains.", 1)

        except Exception as e:
            logger.error(f"Error scraping TLD {tld}: {str(e)}")
            await self.send_progress(f"Error: {str(e)}", 0)
            raise
        finally:
            if self.driver:
                self.driver.quit()

        return domain_list

    def cancel(self):
        """Cancel the scraping operation"""
        self.is_cancelled = True
        if self.driver:
            self.driver.quit()

    def __del__(self):
        """Cleanup: close the browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass 