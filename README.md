# TLD-Domain-Scraper
A Python-based web scraper using Selenium to gather domain names across multiple Top-Level Domains (TLDs) from search engine results.

## Disclaimer
The script involves manual CAPTCHA solving and doesn’t use automated CAPTCHA-solving services or tools,as it generally doesn’t cross the same legal lines. CAPTCHAs exist to verify that a human is interacting with the website. As long as a human (you) is solving the CAPTCHA, it may considered that you're complying with the spirit of the CAPTCHA. Please use it at your own risk.
Even though manual CAPTCHA solving may not violate major laws directly, you still need to be aware of these scenarios:
a) Repeated Access with Automation:

If your script is making repeated requests or scraping data at high speed (even with manual CAPTCHA solving), it may still trigger rate limiting or anti-bot measures on the website. In this case, websites may block your IP or take other defensive measures.
b) Website Policies on Automation:

Many websites forbid any kind of scraping or automated access. Even if you're manually solving CAPTCHAs, if the website’s ToS prohibits the use of bots or automated tools (like Selenium), you may still be violating their terms. For instance, many major websites (including Google, Amazon, and LinkedIn) explicitly prohibit scraping in their ToS.
c) IP Bans or Captive Portals:

Some websites may not only block your IP but also send you to a captive portal (an intermediate page that requests human verification) if they detect repeated automated requests, even if the CAPTCHA is solved manually. This can prevent your script from continuing smoothly.
