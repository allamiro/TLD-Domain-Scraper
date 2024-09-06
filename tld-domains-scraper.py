#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from urllib.parse import urlparse
import time
import random

# Path to ChromeDriver and Google Chrome binary
chrome_driver_path = "/usr/bin/chromedriver"
chrome_binary_path = "/usr/bin/google-chrome"  # Adjust this if necessary

# Set up Chrome options to specify the Chrome binary path
chrome_options = Options()
chrome_options.binary_location = chrome_binary_path

# Set up the Service object for ChromeDriver
service = Service(executable_path=chrome_driver_path)

# Initialize the WebDriver with the service and options
driver = webdriver.Chrome(service=service, options=chrome_options)

# List of TLDs to search
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
    ".EPAGE.IR"
]

# Base query excluding .gov.ir domains
base_query = "-site:.gov.ir"

# Function to extract base domain from URL
def get_base_domain(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"

# Function to detect CAPTCHA (multiple strategies)
def is_captcha_present():
    try:
        captcha_element = driver.find_element(By.XPATH, "//div[@id='captcha'] | //iframe[contains(@src, 'recaptcha')]")
        return True if captcha_element else False
    except:
        return False

# Function to check for "Next" button
def is_next_button_present():
    try:
        next_button = driver.find_element(By.XPATH, "//a[@id='pnnext' or contains(text(), 'Next')]")
        return next_button
    except:
        return None

# Loop through the list of TLDs
for tld in tlds:
    print(f"Scraping domains for TLD: {tld}")
    
    domain_list = set()  # Use a set to store unique domains for each TLD
    
    # Google search query for the current TLD
    query = f"site:{tld} {base_query}"
    url = f"https://www.google.com/search?q={query}"

    # Open the Google search URL
    driver.get(url)
    time.sleep(2)  # Allow the page to load
    
    # Loop through multiple pages (set to 30 pages)
    for page in range(30):  # Adjust this number to match the total number of pages
        # Detect CAPTCHA and pause for manual solving
        if is_captcha_present():
            print("CAPTCHA detected! Please solve it manually in the browser.")
            input("Press Enter after solving the CAPTCHA...")  # Pauses indefinitely until user presses Enter
            print("CAPTCHA solved. Resuming script.")
        
        # Scrape current page's results
        results = driver.find_elements(By.CSS_SELECTOR, 'a')  # Find all links on the page
        print(f"Extracting links from page {page + 1}...")
        
        for link in results:
            href = link.get_attribute('href')
            print(f"Found link: {href}")  # Log the found links for debugging
            if href and tld.lower() in href.lower() and '.gov.ir' not in href and 'translate.google.com' not in href:
                base_domain = get_base_domain(href)
                print(f"Adding domain: {base_domain}")  # Log the added domain
                domain_list.add(base_domain)
        
        # Check for the 'Next' button
        next_button = is_next_button_present()
        
        if next_button:
            next_button.click()
            print(f"Moving to page {page + 1}")
            time.sleep(random.uniform(3, 5))  # Random delay between 3 and 5 seconds
        else:
            print("No more pages or the 'Next' button is missing.")
            break

    # Print all unique collected domain names for the current TLD
    print(f"\nUnique Domain List for {tld}:")
    for domain in domain_list:
        print(domain)

    # Save the unique domain names to a text file named based on the TLD
    tld_clean = tld.replace('.', '').lower()  # Remove dots and lowercase for the filename
    filename = f"iran_{tld_clean}.txt"
    
    with open(filename, "w") as file:
        for domain in sorted(domain_list):  # Sort to keep order
            file.write(domain + "\n")

    print(f"\nDomains for {tld} have been saved to {filename}")

# Close the WebDriver
driver.quit()
