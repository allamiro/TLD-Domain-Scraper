# Python-based Web Scraper for Tracking Domains by TLD (TLD-Domain-Scraper)
A Python-based web scraper using Selenium to gather domain names across multiple Top-Level Domains (TLDs) from search engine results.

## Overview
The idea is to build a Python-based web scraper using Selenium to collect and maintain a list of domain names across multiple Top-Level Domains (TLDs), and country-specific TLDs for example .uk, .fr, .ru, etc. These domain lists can then be used for scraping relevant websites that report or publish information on political changes, events, or disease outbreaks.
![TLD Scrapper workflow](images/tld-scraper.png)
### Application Areas

By targeting specific TLDs and excluding certain government websites (to avoid regulatory or policy conflicts), this tool can build a comprehensive dataset of news websites, blogs, government portals, and NGOs that are likely to provide real-time information on rapidly changing events.
Application Areas

- Monitoring Political Changes:
Elections, protests, policy changes, or international relations often generate a significant amount of online discussion, with articles, reports, and press releases published across many different TLDs.
- Tracking Events or Natural Disasters:
Natural disasters, including earthquakes, floods, and hurricanes, often lead to a spike in online reporting. Local news websites, emergency portals, and community blogs may provide early warnings, first-hand accounts, or official updates.Scraping domains in regions frequently affected by natural disasters (e.g., .au for Australia, .jp for Japan) can enable automated monitoring of related information.
- Following Disease Outbreaks:
Epidemics and pandemics, such as the recent COVID-19 outbreak, produce immense amounts of information from government health agencies, international organizations (e.g., WHO), research institutions, and news outlets. Additionallym different countries may have official health portals.

- Deetect Cyber threats:
  Identify which domains correlate with Cyber threats and bad actors 

- Academic Research:

### Plan
1. Create a list of domain names across various Top-Level Domains (TLDs) by using the Python-based web scraper
2. Process those websites and extract meaningful information: This involves scraping individual pages, organizing the collected data, and preparing it for analysis or indexing into a search engine or analytics platform.
3. Store the scraped content in a structured format.
4. Preprocess the data by cleaning the text if needed
5. Perform language detection and translation to english.
6. Run text analysis techniques, such as Named Entity Recognition (NER) and sentiment analysis techniques.
7. Index the cleaned and processed data into a search engine (e.g., Elasticsearch) or import it into an analytics platform to enable real-time querying and trend analysis.
8. Monitor the data over time to detect emerging patterns or trends
9. Visualize the results


## Dependencies


1. We need a browser driver, such as ChromeDriver for Google Chrome.

* For Fedora /RHEL / RockyLinux

```
dnf install python3 python3-devel chromedriver chrom-browser -y
```

* For Ubuntu

```
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-venv python3-dev chromium-driver chromium-browser -y

```
 

2. Install python libraries


```
python3 -m venv venv
source venv/bin/activate

pip install selenium
pip install requests
```


4. Clone the repository

```
git clone https://github.com/allamiro/TLD-Domain-Scraper.git
cd TLD-Domain-Scraper
```



5. Update these portions of the code to reflect the target tlds  gov sites exclusions and country name you querying: 

I'm using iran tlds that ends with .ir and excluding their gov sites. Complete list of those tlds for each country can be found at https://whoisdatacenter.com/country/ 

```
vim tld-domains-scraper.py
```

```
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

```


```
if href and tld.lower() in href.lower() and '.gov.ir' not in href and 'translate.google.com' not in href:

```



```
filename = f"iran_{tld_clean}.txt"

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

