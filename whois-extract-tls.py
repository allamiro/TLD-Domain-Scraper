#!/usr/bin/env python3

import os
import re
import sys
import time
import random
from html.parser import HTMLParser

import requests

BASE_URL = "https://whoisdatacenter.com/country/"
OUTPUT_FILE = "tlds.txt"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"

COUNTRY_ALIASES = {
    "england": "United Kingdom",
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "united kingdom": "United Kingdom",
}


class CountryLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._current_href = None
        self._current_text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if not href:
            return
        if "/country/" not in href:
            return
        self._current_href = href
        self._current_text = []

    def handle_data(self, data):
        if self._current_href is not None:
            self._current_text.append(data)

    def handle_endtag(self, tag):
        if tag != "a":
            return
        if self._current_href is None:
            return
        text = " ".join(" ".join(self._current_text).split()).strip()
        self.links.append((text, self._current_href))
        self._current_href = None
        self._current_text = []


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self._in_table = False
        self._current_table = []
        self._in_tr = False
        self._current_row = []
        self._in_cell = False
        self._current_cell = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._in_table = True
            self._current_table = []
        elif self._in_table and tag == "tr":
            self._in_tr = True
            self._current_row = []
        elif self._in_tr and tag in ("th", "td"):
            self._in_cell = True
            self._current_cell = []

    def handle_data(self, data):
        if self._in_cell:
            self._current_cell.append(data)

    def handle_endtag(self, tag):
        if tag == "table" and self._in_table:
            if self._current_table:
                self.tables.append(self._current_table)
            self._in_table = False
            self._current_table = []
        elif tag == "tr" and self._in_tr:
            if self._current_row:
                self._current_table.append(self._current_row)
            self._in_tr = False
            self._current_row = []
        elif tag in ("th", "td") and self._in_cell:
            cell_text = " ".join(" ".join(self._current_cell).split()).strip()
            self._current_row.append(cell_text)
            self._in_cell = False
            self._current_cell = []


def fetch_html(url):
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
        timeout=30,
    )
    response.raise_for_status()
    return response.text


def canonicalize_country_name(name):
    if not name:
        return name
    key = name.strip().lower()
    return COUNTRY_ALIASES.get(key, name)


def normalize_country_name(name, href):
    if name:
        return canonicalize_country_name(name)
    slug = href.split("/country/")[-1].strip("/")
    return canonicalize_country_name(slug.replace("-", " "))


def parse_country_links(html):
    parser = CountryLinkParser()
    parser.feed(html)

    candidates = []
    for name, href in parser.links:
        if "/country/" not in href:
            continue
        if href.rstrip("/") == BASE_URL.rstrip("/"):
            continue
        if href.startswith("/"):
            href = "https://whoisdatacenter.com" + href
        candidates.append((normalize_country_name(name, href), href))

    if not candidates:
        for match in re.findall(r'href=["\']([^"\']+/country/[^"\']+)["\']', html):
            if match.rstrip("/") == BASE_URL.rstrip("/"):
                continue
            if match.startswith("/"):
                match = "https://whoisdatacenter.com" + match
            candidates.append((normalize_country_name("", match), match))

    seen = set()
    cleaned = []
    for name, href in candidates:
        slug = href.split("/country/")[-1].strip("/")
        if not slug or slug.lower() in {"gdpr-masked", "private-gdpr-masked"}:
            continue
        if href in seen:
            continue
        seen.add(href)
        cleaned.append((name, href))
    return cleaned


def extract_tlds_from_table(html):
    parser = TableParser()
    parser.feed(html)

    for table in parser.tables:
        header_idx = None
        header_row_index = None
        for idx, row in enumerate(table):
            lowered = [cell.lower() for cell in row]
            if "tld" in lowered:
                header_idx = lowered.index("tld")
                header_row_index = idx
                break
        if header_idx is None:
            continue
        tlds = []
        for row in table[header_row_index + 1 :]:
            if header_idx >= len(row):
                continue
            value = row[header_idx].strip()
            if value.startswith("."):
                tlds.append(value)
        if tlds:
            return tlds
    return []


def extract_tlds_fallback(html):
    pattern = re.compile(r">(\.[A-Za-z0-9.-]{1,30})<")
    found = []
    for match in pattern.findall(html):
        if "/" in match or " " in match:
            continue
        found.append(match.strip())
    return found


def extract_tlds(html):
    tlds = extract_tlds_from_table(html)
    if not tlds:
        tlds = extract_tlds_fallback(html)
    unique = []
    seen = set()
    for tld in tlds:
        if tld in seen:
            continue
        seen.add(tld)
        unique.append(tld)
    return unique


def write_tlds(output_path, country_tlds):
    with open(output_path, "w") as handle:
        handle.write("# Countries\n\n")
        for country, tlds in country_tlds:
            handle.write(f"#{country}\n")
            for tld in tlds:
                handle.write(f"{tld}\n")
            handle.write("\n")


def build_country_urls(args):
    if not args:
        html = fetch_html(BASE_URL)
        return parse_country_links(html)

    custom = []
    for arg in args:
        if arg.startswith("http://") or arg.startswith("https://"):
            name = normalize_country_name("", arg)
            custom.append((name, arg))
            continue
        raw_name = arg.strip()
        canonical_name = canonicalize_country_name(raw_name)
        slug = canonical_name.replace(" ", "-")
        url = f"{BASE_URL}{slug}/"
        custom.append((canonical_name, url))
    return custom


def main():
    countries = build_country_urls(sys.argv[1:])
    if not countries:
        print("No countries found to process.")
        return

    collected = []
    for idx, (country, url) in enumerate(countries, start=1):
        print(f"[{idx}/{len(countries)}] Fetching {country}: {url}")
        try:
            html = fetch_html(url)
        except requests.RequestException as exc:
            print(f"  Failed to fetch {country}: {exc}")
            continue
        tlds = extract_tlds(html)
        if not tlds:
            print(f"  No TLDs found for {country}")
            continue
        collected.append((country, tlds))
        time.sleep(random.uniform(0.5, 1.5))

    output_path = os.path.join(os.path.dirname(__file__), OUTPUT_FILE)
    write_tlds(output_path, collected)
    print(f"Saved {len(collected)} countries to {output_path}")


if __name__ == "__main__":
    main()
