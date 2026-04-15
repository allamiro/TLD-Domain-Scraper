from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SearchEngine:
    """Configuration for one search engine backend."""
    key: str                          # internal identifier
    display_name: str                 # shown in the UI
    search_url: str                   # Python format string — {tld} is substituted
    next_xpath: str                   # XPath that locates the "next page" element
    excluded_in_results: list[str]    # URL fragments to discard from scraped links
    max_pages: int = 10               # hard page limit per TLD


# ---------------------------------------------------------------------------
# Engine definitions
# ---------------------------------------------------------------------------

GOOGLE = SearchEngine(
    key="google",
    display_name="Google",
    # &num=100 requests 100 results per page (Google's maximum)
    # &hl=en ensures a consistent English UI so XPath selectors stay stable
    search_url="https://www.google.com/search?q=site:{tld}+-site:.gov.ir&num=100&hl=en",
    next_xpath="//a[@id='pnnext']",
    excluded_in_results=[
        "google.com", "translate.google.com", "webcache.googleusercontent.com",
    ],
)

BING = SearchEngine(
    key="bing",
    display_name="Bing",
    # &count=50 is Bing's maximum per page
    # &setlang=en for a stable English UI
    search_url="https://www.bing.com/search?q=site:{tld}+-site:.gov.ir&count=50&setlang=en",
    next_xpath=(
        "//a[@aria-label='Next page']"
        " | //a[contains(@class,'sb_pagN')]"
        " | //a[contains(@class,'b_widePag') and contains(text(),'Next')]"
    ),
    excluded_in_results=[
        "bing.com", "microsoft.com", "msn.com",
    ],
)

DUCKDUCKGO = SearchEngine(
    key="duckduckgo",
    display_name="DuckDuckGo",
    # HTML (non-JS) endpoint — reliable for headless scraping
    search_url="https://html.duckduckgo.com/html/?q=site:{tld}+-site:.gov.ir",
    # DDG uses a form submit button, not an anchor — execute_script click works fine
    next_xpath="//input[@type='submit' and @value='Next']",
    excluded_in_results=[
        "duckduckgo.com", "duck.com",
    ],
    max_pages=5,   # DDG returns ~30 results/page and caps earlier than Bing/Google
)

YANDEX = SearchEngine(
    key="yandex",
    display_name="Yandex",
    # numdoc=50 requests 50 results per page; lr=10513 = Iran region boost
    search_url=(
        "https://yandex.com/search/?text=site:{tld}+-site:.gov.ir"
        "&numdoc=50&lang=en"
    ),
    next_xpath=(
        "//a[contains(@class,'pager__item_kind_next')]"
        " | //a[@aria-label='Next page']"
        " | //a[contains(@class,'n-pager') and contains(@class,'next')]"
    ),
    excluded_in_results=[
        "yandex.com", "yandex.ru", "ya.ru",
    ],
)


# Registry — ordered by expected yield for .ir / Middle-Eastern TLDs
ALL_ENGINES: dict[str, SearchEngine] = {
    e.key: e for e in [GOOGLE, BING, DUCKDUCKGO, YANDEX]
}

DEFAULT_ENGINES: list[str] = ["google", "bing"]


def get_engines(keys: list[str]) -> list[SearchEngine]:
    """Return engine objects for the given keys, preserving order."""
    return [ALL_ENGINES[k] for k in keys if k in ALL_ENGINES]
