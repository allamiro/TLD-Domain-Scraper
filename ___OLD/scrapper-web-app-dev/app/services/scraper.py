import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, NoSuchElementException, WebDriverException
from urllib.parse import urlparse
import time
import random
from typing import List, Set, Optional
import logging
from fastapi import WebSocket
import os
import socket
from urllib3.exceptions import NewConnectionError

logger = logging.getLogger(__name__)

class DomainScraper:
    def __init__(self, websocket: Optional[WebSocket] = None):
        self.current_os = platform.system()
        self.websocket = websocket
        self.is_cancelled = False
        self.driver = None
        self.wait = None
        self._setup_chrome_driver()
        
    def _setup_chrome_driver(self, max_retries: int = 3):
        """Setup Chrome driver based on operating system with retry logic"""
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                if self.current_os == "Darwin":  # macOS
                    chrome_driver_path = "/opt/homebrew/bin/chromedriver"  # Typical path for chromedriver on macOS
                    chrome_binary_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                elif self.current_os == "Linux":
                    chrome_driver_path = "/usr/bin/chromedriver"
                    chrome_binary_path = "/usr/bin/google-chrome"
                elif self.current_os == "Windows":
                    chrome_driver_path = "C:\\path\\to\\chromedriver.exe"
                    chrome_binary_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
                else:
                    raise Exception(f"Unsupported OS: {self.current_os}")

                if not os.path.exists(chrome_driver_path):
                    raise Exception(f"ChromeDriver not found at {chrome_driver_path}. Please install it using Homebrew: brew install chromedriver")

                chrome_options = Options()
                chrome_options.binary_location = chrome_binary_path
                
                # Configure window size and position
                chrome_options.add_argument("--window-size=800,600")
                chrome_options.add_argument("--window-position=0,0")  # Position on the left side
                
                # Additional options for better scraping
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--remote-debugging-port=9222")  # Enable remote debugging
                
                # Add user agent to avoid detection
                chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                
                service = Service(executable_path=chrome_driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.wait = WebDriverWait(self.driver, 10)  # 10 seconds timeout
                return  # Successfully initialized

            except (WebDriverException, NewConnectionError, socket.error) as e:
                last_error = e
                retry_count += 1
                logger.warning(f"Failed to initialize ChromeDriver (attempt {retry_count}/{max_retries}): {str(e)}")
                
                # Clean up any partially initialized driver
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None
                
                # Wait before retrying
                time.sleep(2)
        
        # If we get here, all retries failed
        raise Exception(f"Failed to initialize ChromeDriver after {max_retries} attempts. Last error: {str(last_error)}")

    async def _send_progress(self, message: str, progress: float = None):
        """Send progress update through WebSocket"""
        if self.websocket:
            try:
                await self.websocket.send_json({
                    "message": message,
                    "progress": progress
                })
            except Exception as e:
                logger.error(f"Failed to send progress update: {e}")

    def _is_captcha_present(self):
        """Check if CAPTCHA is present on the page"""
        try:
            # Wait for CAPTCHA elements with a shorter timeout
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='captcha'] | //iframe[contains(@src, 'recaptcha')]"))
            )
            return True
        except TimeoutException:
            return False

    def _is_next_button_present(self):
        """Check if next button is present and clickable"""
        try:
            next_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[@id='pnnext' or contains(text(), 'Next')]"))
            )
            return next_button
        except (TimeoutException, ElementNotInteractableException):
            return None

    def _get_base_domain(self, url: str) -> str:
        """Extract base domain from URL"""
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}"

    async def scrape_tld(self, tld: str) -> Set[str]:
        """Scrape domains for a specific TLD"""
        domain_list = set()
        base_query = "-site:.gov.ir"
        query = f"site:{tld} {base_query}"
        url = f"https://www.google.com/search?q={query}"

        try:
            # Ensure driver is still valid
            if not self.driver:
                self._setup_chrome_driver()

            self.driver.get(url)
            await self._send_progress(f"Starting scrape for TLD: {tld}", 0.0)
            time.sleep(2)  # Initial page load

            for page in range(30):
                if self.is_cancelled:
                    await self._send_progress("Scraping cancelled by user", 0.0)
                    break

                # Check for CAPTCHA
                if self._is_captcha_present():
                    await self._send_progress("CAPTCHA detected! Please solve it manually.", 0.0)
                    input("Press Enter after solving the CAPTCHA...")
                    await self._send_progress("CAPTCHA solved, resuming...", 0.0)
                    time.sleep(2)  # Wait for page to stabilize after CAPTCHA

                # Wait for search results to load
                try:
                    self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.g'))
                    )
                except TimeoutException:
                    await self._send_progress("No search results found", 0.0)
                    break

                # Scrape current page
                results = self.driver.find_elements(By.CSS_SELECTOR, 'a')
                for link in results:
                    try:
                        href = link.get_attribute('href')
                        if href and tld.lower() in href.lower() and '.gov.ir' not in href and 'translate.google.com' not in href:
                            base_domain = self._get_base_domain(href)
                            domain_list.add(base_domain)
                            await self._send_progress(f"Found domain: {base_domain}", 0.0)
                    except Exception as e:
                        logger.error(f"Error processing link: {e}")
                        continue

                # Try to click next button
                next_button = self._is_next_button_present()
                if next_button:
                    try:
                        next_button.click()
                        await self._send_progress(f"Moving to page {page + 1}", 0.0)
                        time.sleep(random.uniform(3, 5))  # Random delay between pages
                    except Exception as e:
                        logger.error(f"Error clicking next button: {e}")
                        break
                else:
                    await self._send_progress("No more pages available", 0.0)
                    break

            await self._send_progress(f"Completed scraping for {tld}. Found {len(domain_list)} domains.", 1.0)
            return domain_list

        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            await self._send_progress(f"Error: {str(e)}", 0.0)
            raise
        finally:
            # Clean up the driver in case of errors
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None

    def cancel(self):
        """Cancel the scraping operation"""
        self.is_cancelled = True
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

    def __del__(self):
        """Cleanup when the scraper is destroyed"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass 