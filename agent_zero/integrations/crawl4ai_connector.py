#!/usr/bin/env python3
"""
Agent Zero Integration — crawl4ai (FULL IMPLEMENTATION)
Category : SCRAPER / PERCEPTION
Source   : https://github.com/unclecode/crawl4ai
Stars    : 67,628
Absorbed : 2026-06-02

What it does:
    Turns ANY URL into clean, LLM-ready Markdown in one call.
    Battle-tested by a 50K+ community. Async, fast, Playwright-backed.
    Built specifically for RAG pipelines, agents, and data extraction.

Pantheon Role:
    Agent Zero's PERCEPTION LAYER for the open web.
    ScoutPrime uses this to read property listings, auctions, comps.
    GhostPrime uses this to read social signal pages.
    ContentPrime uses this to extract trending niche data.
    Any Prime that needs to READ the web goes through here.

Install:
    pip install crawl4ai
    crawl4ai-setup   (installs Playwright browsers)

Usage:
    connector = Crawl4AIConnector()
    result = connector.scrape("https://example.com")
    print(result["markdown"])
"""

import os
import json
import asyncio
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import urllib.request


# ─── TELEGRAM CONFIG ─────────────────────────────────────────────────────────

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8679655550:AAGUB1m5fmqHc8OHqqM24Vixz8FfwX-gqD4")
TELEGRAM_CHAT  = os.environ.get("TELEGRAM_CHAT_ID", "7135054241")


# ─── INSTALL HELPER ──────────────────────────────────────────────────────────

def ensure_installed() -> bool:
    try:
        import crawl4ai
        return True
    except ImportError:
        print("[crawl4ai] Not installed. Installing...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "crawl4ai"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"[crawl4ai] pip install failed: {result.stderr[-300:]}")
            return False
        # Run setup (installs Playwright browsers)
        subprocess.run(["crawl4ai-setup"], capture_output=True)
        return True


# ─── CORE CONNECTOR ──────────────────────────────────────────────────────────

class Crawl4AIConnector:
    """
    Pantheon connector for crawl4ai.
    Turns any URL into clean LLM-ready Markdown.
    Agent Zero's perception layer for the open web.
    """

    REPO_URL = "https://github.com/unclecode/crawl4ai"
    CATEGORY = "SCRAPER"
    PANTHEON_ROLE = "PERCEPTION"

    def __init__(self, headless: bool = True, verbose: bool = False):
        self.headless = headless
        self.verbose  = verbose
        self._ready   = ensure_installed()

    # ── LIFECYCLE ─────────────────────────────────────────────────────────────

    def health_check(self) -> Dict:
        return {
            "name":        "crawl4ai",
            "category":    self.CATEGORY,
            "role":        self.PANTHEON_ROLE,
            "ready":       self._ready,
            "status":      "ok" if self._ready else "not_installed",
            "stars":       67628,
        }

    # ── SINGLE URL ────────────────────────────────────────────────────────────

    def scrape(self, url: str, extract_links: bool = False,
               css_selector: Optional[str] = None,
               word_count_threshold: int = 10) -> Dict:
        """
        Scrape a single URL and return clean Markdown + metadata.

        :param url:                  Target URL
        :param extract_links:        Include all links found on the page
        :param css_selector:         Optional CSS selector to scope extraction
        :param word_count_threshold: Min words per content block (filters noise)
        :return:                     Pantheon signal dict with markdown, links, metadata
        """
        if not self._ready:
            return {"error": "crawl4ai not installed", "status": "failed"}

        return asyncio.run(self._async_scrape(url, extract_links, css_selector, word_count_threshold))

    async def _async_scrape(self, url, extract_links, css_selector, word_count_threshold):
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

        browser_cfg = BrowserConfig(headless=self.headless, verbose=self.verbose)
        run_cfg     = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            word_count_threshold=word_count_threshold,
            css_selector=css_selector,
            extract_links=extract_links,
        )

        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(url=url, config=run_cfg)

        return self.to_pantheon_signal({
            "url":      url,
            "status":   "ok" if result.success else "failed",
            "markdown": result.markdown if result.success else None,
            "links":    result.links if extract_links and result.success else [],
            "error":    result.error_message if not result.success else None,
            "metadata": {
                "title":       getattr(result, "metadata", {}).get("title", ""),
                "status_code": getattr(result, "status_code", None),
            }
        })

    # ── BATCH / DEEP CRAWL ────────────────────────────────────────────────────

    def scrape_many(self, urls: List[str], **kwargs) -> List[Dict]:
        """
        Scrape multiple URLs in parallel (async batch).
        Returns a list of Pantheon signal dicts.
        """
        if not self._ready:
            return [{"error": "crawl4ai not installed", "status": "failed"}]
        return asyncio.run(self._async_scrape_many(urls, **kwargs))

    async def _async_scrape_many(self, urls, **kwargs):
        tasks = [self._async_scrape(url, False, None, 10) for url in urls]
        return await asyncio.gather(*tasks)

    def deep_crawl(self, start_url: str, max_depth: int = 2,
                   max_pages: int = 20) -> List[Dict]:
        """
        Deep crawl from a starting URL, following internal links.
        Useful for reading full sites (auction listings, property portals, etc.)

        :param start_url: Root URL to start from
        :param max_depth: How many link-hops to follow
        :param max_pages: Hard cap on pages crawled
        :return:          List of Pantheon signal dicts, one per page
        """
        if not self._ready:
            return [{"error": "crawl4ai not installed", "status": "failed"}]
        return asyncio.run(self._async_deep_crawl(start_url, max_depth, max_pages))

    async def _async_deep_crawl(self, start_url, max_depth, max_pages):
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
        from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

        browser_cfg = BrowserConfig(headless=self.headless, verbose=self.verbose)
        run_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            deep_crawl_strategy=BFSDeepCrawlStrategy(
                max_depth=max_depth,
                max_pages=max_pages,
                include_external=False,
            ),
        )

        results = []
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            async for result in await crawler.arun(url=start_url, config=run_cfg):
                results.append(self.to_pantheon_signal({
                    "url":      result.url,
                    "status":   "ok" if result.success else "failed",
                    "markdown": result.markdown if result.success else None,
                    "depth":    getattr(result, "depth", None),
                    "error":    result.error_message if not result.success else None,
                }))
        return results

    # ── LLM EXTRACTION ────────────────────────────────────────────────────────

    def extract_structured(self, url: str, schema: Dict,
                            instruction: str = "") -> Dict:
        """
        Use crawl4ai's LLM extraction to pull structured data from a page.
        Provide a JSON schema and optional instruction.

        Example schema for property data:
            {
                "address":  {"type": "string"},
                "price":    {"type": "number"},
                "bedrooms": {"type": "integer"},
                "sqft":     {"type": "number"}
            }
        """
        if not self._ready:
            return {"error": "crawl4ai not installed", "status": "failed"}
        return asyncio.run(self._async_extract(url, schema, instruction))

    async def _async_extract(self, url, schema, instruction):
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
        from crawl4ai.extraction_strategy import LLMExtractionStrategy

        strategy = LLMExtractionStrategy(
            schema=schema,
            instruction=instruction or "Extract the requested fields from this page.",
        )
        browser_cfg = BrowserConfig(headless=self.headless)
        run_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=strategy,
        )

        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(url=url, config=run_cfg)

        extracted = {}
        if result.success and result.extracted_content:
            try:
                extracted = json.loads(result.extracted_content)
            except Exception:
                extracted = {"raw": result.extracted_content}

        return self.to_pantheon_signal({
            "url":       url,
            "status":    "ok" if result.success else "failed",
            "extracted": extracted,
            "markdown":  result.markdown if result.success else None,
        })

    # ── PANTHEON PRIME SHORTCUTS ───────────────────────────────────────────────

    def scout_property(self, listing_url: str) -> Dict:
        """
        ScoutPrime shortcut: extract property data from a listing URL.
        Returns structured address, price, beds, baths, sqft.
        """
        schema = {
            "address":      {"type": "string"},
            "price":        {"type": "number"},
            "bedrooms":     {"type": "integer"},
            "bathrooms":    {"type": "number"},
            "sqft":         {"type": "number"},
            "auction_date": {"type": "string"},
            "description":  {"type": "string"},
        }
        return self.extract_structured(
            listing_url, schema,
            instruction="Extract property listing details: address, price, bedrooms, bathrooms, square footage, auction date if present, and description."
        )

    def ghost_read_signal(self, url: str) -> Dict:
        """
        GhostPrime shortcut: read a social/news page and return clean markdown
        for sentiment analysis and signal injection.
        """
        return self.scrape(url, extract_links=False, word_count_threshold=20)

    def content_niche_scan(self, urls: List[str]) -> List[Dict]:
        """
        ContentPrime shortcut: batch-scrape niche research URLs
        and return clean markdown for each.
        """
        return self.scrape_many(urls)

    # ── PANTHEON SIGNAL + RELAY ───────────────────────────────────────────────

    def to_pantheon_signal(self, raw: Any) -> Dict:
        return {
            "source":    "crawl4ai",
            "category":  self.CATEGORY,
            "role":      self.PANTHEON_ROLE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data":      raw,
        }

    def relay_to_telegram(self, message: str) -> None:
        payload = {"chat_id": TELEGRAM_CHAT, "text": f"[crawl4ai] {message}", "parse_mode": "Markdown"}
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data=data, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.loads(r.read())
        except Exception as e:
            print(f"[crawl4ai] Telegram relay failed: {e}")


# ─── CLI / QUICK TEST ────────────────────────────────────────────────────────

if __name__ == "__main__":
    connector = Crawl4AIConnector()
    print(json.dumps(connector.health_check(), indent=2))

    if len(sys.argv) > 1:
        url = sys.argv[1]
        print(f"\nScraping: {url}")
        result = connector.scrape(url)
        if result["data"]["status"] == "ok":
            md = result["data"]["markdown"] or ""
            print(f"\n--- MARKDOWN ({len(md)} chars) ---")
            print(md[:2000])
        else:
            print(f"Error: {result['data'].get('error')}")
