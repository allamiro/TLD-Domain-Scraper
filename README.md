# TLD-Domain-Scraper
A Python-based web scraper using Selenium to gather domain names across multiple Top-Level Domains (TLDs) from search engine results.

## Dependencies


1. We need a browser driver, such as ChromeDriver for Google Chrome.

```
dnf install python3 python3-devel chromedriver chrom-browser -y
```


2. Install python libraries

```
pip install selenium
pip install requests
```


## Disclaimer

This project is provided for **educational purposes only**. The creators and contributors of this project are not responsible for any misuse or illegal activities performed with this code.

The script involves manual CAPTCHA solving and doesn’t use automated CAPTCHA-solving services or tools,as it generally doesn’t cross the same legal lines. CAPTCHAs exist to verify that a human is interacting with the website. As long as a human (you) is solving the CAPTCHA, it may considered that you're complying with the spirit of the CAPTCHA. 

Even though manual CAPTCHA solving may not violate major laws directly, you still need to be aware of these scenarios:

a) Repeated Access with Automation:

If your script is making repeated requests or scraping data at high speed (even with manual CAPTCHA solving), it may still trigger rate limiting or anti-bot measures on the website. In this case, websites may block your IP or take other defensive measures.

b) Website Policies on Automation:

Many websites forbid any kind of scraping or automated access. Even if you're manually solving CAPTCHAs, if the website’s ToS prohibits the use of bots or automated tools (like Selenium), you may still be violating their terms. For instance, many major websites (including Google, Amazon, and LinkedIn) explicitly prohibit scraping in their ToS.

c) IP Bans or Captive Portals:

Some websites may not only block your IP but also send you to a captive portal (an intermediate page that requests human verification) if they detect repeated automated requests, even if the CAPTCHA is solved manually. This can prevent your script from continuing smoothly.



### Responsibilities of the User:
- It is your responsibility to ensure that your use of this tool complies with all relevant laws, regulations, and terms of service of the websites or platforms you interact with.
- The use of this tool to scrape data or bypass protections such as CAPTCHAs may violate the **Terms of Service** of certain websites. Please consult the applicable policies before using this tool.
- This tool is provided "as is", without any warranty of any kind, express or implied. The developers are not responsible for any damage or liability arising from the use or inability to use this tool.

### No Warranty:
This tool is provided **without any warranties**, whether express or implied, including but not limited to the implied warranties of merchantability, fitness for a particular purpose, or non-infringement.

### Use at Your Own Risk:
By using this tool, you agree to use it at your own risk. The developers assume no liability for any legal or financial consequences resulting from the misuse or abuse of this tool.

