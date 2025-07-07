#!/usr/bin/env python3
"""
Advanced Price Comparison Scraper CLI Tool
Created by: Sneha Jajodia

A comprehensive CLI tool that scrapes multiple e-commerce websites
for price comparisons across different countries with stealth features.
"""

import argparse
import json
import logging
import random
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('price_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ProductResult:
    """Data class for product search results"""
    link: str
    price: str
    currency: str
    product_name: str
    website: str
    rating: Optional[str] = None
    availability: Optional[str] = None
    original_price: Optional[str] = None
    discount_percentage: Optional[str] = None

class AdvancedPriceScraper:
    """Advanced price comparison scraper with stealth features"""
    
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
        ]
        
        self.locales = ['en-US', 'en-IN', 'en-GB', 'en-CA', 'en-AU', 'hi-IN']
        
        # Comprehensive website configurations
        self.website_configs = {
            "US": {
                "amazon": {
                    "base_url": "https://www.amazon.com",
                    "search_url": "https://www.amazon.com/s?k={query}",
                    "selectors": {
                        "product_container": "div[data-component-type='s-search-result']",
                        "product_name": "h2 span",
                        "price": "span.a-price > span.a-offscreen",
                        "currency": "USD",
                        "link": "h2 a"
                    }
                },
                "walmart": {
                    "base_url": "https://www.walmart.com",
                    "search_url": "https://www.walmart.com/search?q={query}",
                    "selectors": {
                        "product_container": "div[data-type='items'] div[data-item-id]",
                        "product_name": "span.lh-title",
                        "price": "span.price-characteristic",
                        "currency": "USD",
                        "link": "a.absolute"
                    }
                },
                "target": {
                    "base_url": "https://www.target.com",
                    "search_url": "https://www.target.com/s?searchTerm={query}",
                    "selectors": {
                        "product_container": "div[data-test='product-card']",
                        "product_name": "a[data-test='product-title']",
                        "price": "span[data-test='current-price']",
                        "currency": "USD",
                        "link": "a[data-test='product-title']"
                    }
                },
                "ebay": {
                    "base_url": "https://www.ebay.com",
                    "search_url": "https://www.ebay.com/sch/i.html?_nkw={query}",
                    "selectors": {
                        "product_container": "div.s-item__info",
                        "product_name": "div.s-item__title",
                        "price": "span.s-item__price",
                        "currency": "USD",
                        "link": "a.s-item__link"
                    }
                }
            },
            "IN": {
                "amazon": {
                    "base_url": "https://www.amazon.in",
                    "search_url": "https://www.amazon.in/s?k={query}",
                    "selectors": {
                        "product_container": "div[data-component-type='s-search-result']",
                        "product_name": "h2 span",
                        "price": "span.a-price > span.a-offscreen",
                        "currency": "INR",
                        "link": "h2 a"
                    }
                },
                "flipkart": {
                    "base_url": "https://www.flipkart.com",
                    "search_url": "https://www.flipkart.com/search?q={query}",
                    "selectors": {
                        "product_container": "div._75nlfW",
                        "product_name": "div.KzDlHZ",
                        "price": "div.Nx9bqj",
                        "currency": "INR",
                        "link": "a.CGtC98"
                    }
                },
                "myntra": {
                    "base_url": "https://www.myntra.com",
                    "search_url": "https://www.myntra.com/{query}",
                    "selectors": {
                        "product_container": "li.product-base",
                        "product_name": "h3.product-brand",
                        "price": "span.product-discountedPrice",
                        "currency": "INR",
                        "link": "a.product-base-link"
                    }
                },
                "ajio": {
                    "base_url": "https://www.ajio.com",
                    "search_url": "https://www.ajio.com/search/?text={query}",
                    "selectors": {
                        "product_container": "div.item rilrtl-products-list__item",
                        "product_name": "div.nameCls",
                        "price": "span.price",
                        "currency": "INR",
                        "link": "a.rilrtl-products-list__link"
                    }
                }
            },
            "UK": {
                "amazon": {
                    "base_url": "https://www.amazon.co.uk",
                    "search_url": "https://www.amazon.co.uk/s?k={query}",
                    "selectors": {
                        "product_container": "div[data-component-type='s-search-result']",
                        "product_name": "h2 span",
                        "price": "span.a-price > span.a-offscreen",
                        "currency": "GBP",
                        "link": "h2 a"
                    }
                },
                "argos": {
                    "base_url": "https://www.argos.co.uk",
                    "search_url": "https://www.argos.co.uk/search/{query}/",
                    "selectors": {
                        "product_container": "div[data-test='product-card']",
                        "product_name": "a[data-test='product-card-title']",
                        "price": "span[data-test='product-card-price']",
                        "currency": "GBP",
                        "link": "a[data-test='product-card-title']"
                    }
                },
                "currys": {
                    "base_url": "https://www.currys.co.uk",
                    "search_url": "https://www.currys.co.uk/search?q={query}",
                    "selectors": {
                        "product_container": "div.product-tile",
                        "product_name": "h3.product-name",
                        "price": "span.price",
                        "currency": "GBP",
                        "link": "a.product-link"
                    }
                }
            },
            "CA": {
                "amazon": {
                    "base_url": "https://www.amazon.ca",
                    "search_url": "https://www.amazon.ca/s?k={query}",
                    "selectors": {
                        "product_container": "div[data-component-type='s-search-result']",
                        "product_name": "h2 span",
                        "price": "span.a-price > span.a-offscreen",
                        "currency": "CAD",
                        "link": "h2 a"
                    }
                },
                "walmart": {
                    "base_url": "https://www.walmart.ca",
                    "search_url": "https://www.walmart.ca/search?q={query}",
                    "selectors": {
                        "product_container": "div[data-type='items'] div[data-item-id]",
                        "product_name": "span.lh-title",
                        "price": "span.price-characteristic",
                        "currency": "CAD",
                        "link": "a.absolute"
                    }
                }
            }
        }
    
    def extract_price(self, price_text: str) -> str:
        """Extract numeric price from text"""
        if not price_text:
            return "0"
        
        # Remove currency symbols and commas
        price_text = re.sub(r'[^\d.,]', '', price_text)
        
        # Handle different price formats
        if ',' in price_text:
            price_text = price_text.replace(',', '')
        
        # Extract first number found
        match = re.search(r'(\d+(?:\.\d+)?)', price_text)
        if match:
            return match.group(1)
        
        return "0"
    
    def detect_captcha(self, page: Page) -> bool:
        """Detect if page contains CAPTCHA"""
        try:
            html = page.content().lower()
            captcha_indicators = [
                "captcha", "verify you are human", "robot check", 
                "security check", "please verify", "prove you're not a robot",
                "enter the characters you see below", "cloudflare"
            ]
            
            for indicator in captcha_indicators:
                if indicator in html:
                    logger.warning(f"Detected CAPTCHA page with indicator: {indicator}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error detecting CAPTCHA: {e}")
            return False
    
    def simulate_human_behavior(self, page: Page):
        """Simulate realistic human browsing behavior"""
        try:
            # Random viewport size
            viewport_width = random.randint(1200, 1800)
            viewport_height = random.randint(800, 1200)
            page.set_viewport_size({"width": viewport_width, "height": viewport_height})
            
            # Random mouse movements
            for _ in range(random.randint(3, 7)):
                x = random.randint(100, viewport_width - 100)
                y = random.randint(100, viewport_height - 100)
                page.mouse.move(x, y)
                time.sleep(random.uniform(0.1, 0.5))
            
            # Random scrolling with pauses
            for _ in range(random.randint(3, 6)):
                scroll_amount = random.randint(300, 800)
                page.mouse.wheel(0, scroll_amount)
                time.sleep(random.uniform(0.5, 2.0))
                
                # Sometimes scroll back up a bit
                if random.random() < 0.3:
                    page.mouse.wheel(0, -random.randint(100, 300))
                    time.sleep(random.uniform(0.3, 1.0))
                    
        except Exception as e:
            logger.warning(f"Error in human behavior simulation: {e}")
    
    def create_stealth_context(self, browser: Browser, country: str) -> BrowserContext:
        """Create a stealth browser context"""
        # Get timezone based on country
        timezone_map = {
            "US": "America/New_York",
            "IN": "Asia/Kolkata", 
            "UK": "Europe/London",
            "CA": "America/Toronto"
        }
        timezone = timezone_map.get(country, "UTC")
        
        context = browser.new_context(
            user_agent=random.choice(self.user_agents),
            viewport={'width': random.randint(1200, 1800), 'height': random.randint(800, 1200)},
            java_script_enabled=True,
            locale=random.choice(self.locales),
            timezone_id=timezone,
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
        )
        
        # Add stealth scripts to hide automation
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            Object.defineProperty(navigator, 'permissions', {
                get: () => ({
                    query: () => Promise.resolve({ state: 'granted' })
                }),
            });
            window.chrome = {
                runtime: {},
            };
        """)
        
        return context
    
    def search_website(self, config: Dict, query: str, max_results: int = 10, headless: bool = True) -> List[ProductResult]:
        """Search a specific website for products with enhanced stealth mode"""
        results = []
        
        try:
            with sync_playwright() as p:
                # Launch browser with enhanced stealth options
                browser = p.chromium.launch(
                    headless=headless,
                    args=[
                        "--no-sandbox",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--disable-web-security",
                        "--disable-features=VizDisplayCompositor",
                        "--disable-extensions",
                        "--disable-plugins",
                        "--disable-images",  # Faster loading
                    ]
                )
                
                # Create stealth context
                context = self.create_stealth_context(browser, "IN" if "in" in config['base_url'] else "US")
                page = context.new_page()
                
                # Navigate to search page
                search_url = config["search_url"].format(query=query.replace(' ', '+'))
                logger.info(f"Navigating to: {search_url}")
                
                page.goto(search_url, timeout=60000, wait_until='domcontentloaded')
                page.wait_for_load_state('networkidle', timeout=30000)
                
                selectors = config["selectors"]
                
                # Additional wait for dynamic content
                try:
                    page.wait_for_selector(selectors["product_container"], timeout=10000)
                    logger.info(f"Found product container selector: {selectors['product_container']}")
                except Exception as e:
                    logger.warning(f"Product container selector not found: {e}")
                
                # Save the HTML for debugging
                html_file = f"{config['base_url'].split('//')[1].split('.')[1]}_{query.replace(' ', '_')}.html"
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(page.content())
                logger.info(f"Saved page HTML to {html_file}")
                
                if self.detect_captcha(page):
                    logger.warning(f"CAPTCHA detected on {config['base_url']}. Skipping...")
                    browser.close()
                    return []
                
                # Simulate human behavior
                self.simulate_human_behavior(page)
                
                containers = page.query_selector_all(selectors["product_container"])
                logger.info(f"Found {len(containers)} product containers on {config['base_url']}")
                
                for container in containers[:max_results]:
                    try:
                        # Extract product name
                        name_elem = container.query_selector(selectors["product_name"])
                        if not name_elem:
                            continue
                        product_name = name_elem.inner_text().strip()
                        
                        if not product_name:
                            continue
                        
                        # Extract price
                        price_elem = container.query_selector(selectors["price"])
                        if not price_elem:
                            continue
                        price_text = price_elem.inner_text().strip()
                        price = self.extract_price(price_text)
                        
                        if price == "0":
                            continue
                        
                        # Extract link
                        link_elem = container.query_selector(selectors["link"])
                        if not link_elem:
                            continue
                        href = link_elem.get_attribute("href")
                        if not href:
                            continue
                        
                        link = f"{config['base_url']}{href}" if href.startswith('/') else href
                        
                        # Create result
                        result = ProductResult(
                            link=link,
                            price=price,
                            currency=selectors["currency"],
                            product_name=product_name,
                            website=config["base_url"].split("//")[1].split(".")[1]
                        )
                        
                        results.append(result)
                        logger.info(f"Found product: {product_name[:50]}... - {price}")
                        
                    except Exception as e:
                        logger.warning(f"Error parsing product: {e}")
                        continue
                
                browser.close()
                
        except Exception as e:
            logger.error(f"Error searching {config['base_url']}: {e}")
        
        return results
    
    def check_existing_links(self, file_path: str, headless: bool = True) -> List[ProductResult]:
        """Check prices for existing links from a JSON file"""
        results = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_products = json.load(f)
            
            logger.info(f"Loaded {len(existing_products)} products from {file_path}")
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=headless)
                context = self.create_stealth_context(browser, "US")
                page = context.new_page()
                
                for product in existing_products:
                    try:
                        logger.info(f"Checking price for: {product.get('productName', 'Unknown')}")
                        
                        page.goto(product['link'], timeout=30000, wait_until='domcontentloaded')
                        page.wait_for_load_state('networkidle', timeout=15000)
                        
                        if self.detect_captcha(page):
                            logger.warning(f"CAPTCHA detected for {product['link']}")
                            continue
                        
                        # Try to find price on the product page
                        price_selectors = [
                            "span[data-price]",
                            ".price",
                            "[class*='price']",
                            "span[class*='Price']",
                            ".product-price"
                        ]
                        
                        current_price = product.get('price', '0')
                        for selector in price_selectors:
                            try:
                                price_elem = page.query_selector(selector)
                                if price_elem:
                                    price_text = price_elem.inner_text().strip()
                                    extracted_price = self.extract_price(price_text)
                                    if extracted_price != "0":
                                        current_price = extracted_price
                                        break
                            except:
                                continue
                        
                        # Create updated result
                        result = ProductResult(
                            link=product['link'],
                            price=current_price,
                            currency=product.get('currency', 'USD'),
                            product_name=product.get('productName', 'Unknown'),
                            website=urlparse(product['link']).netloc.split('.')[1]
                        )
                        
                        results.append(result)
                        
                        # Random delay between requests
                        time.sleep(random.uniform(2, 5))
                        
                    except Exception as e:
                        logger.error(f"Error checking {product.get('link', 'Unknown')}: {e}")
                        continue
                
                browser.close()
                
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
        
        return results
    
    def search_products(self, country: str, query: str, file_path: Optional[str] = None, 
                       max_results_per_site: int = 10, headless: bool = True) -> List[Dict]:
        """Main search function with enhanced features"""
        logger.info(f"Searching for '{query}' in {country}")
        
        if country not in self.website_configs:
            raise ValueError(f"Country {country} not supported")
        
        all_results = []
        
        # If file path provided, check existing links first
        if file_path and Path(file_path).exists():
            logger.info(f"Checking existing links from {file_path}")
            existing_results = self.check_existing_links(file_path, headless)
            all_results.extend(existing_results)
        
        # Search websites
        for site_name, config in self.website_configs[country].items():
            logger.info(f"Searching {site_name}...")
            
            try:
                site_results = self.search_website(config, query, max_results_per_site, headless)
                all_results.extend(site_results)
                
                # Add delay between sites
                delay = random.uniform(3, 6)
                logger.info(f"Waiting {delay:.1f} seconds before next site...")
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Failed to search {site_name}: {e}")
        
        # Filter and sort results
        valid_results = []
        for result in all_results:
            # Filter out results with no price or invalid price
            if result.price and result.price != "0" and result.link:
                valid_results.append(result)
        
        # Sort by price (ascending)
        valid_results.sort(key=lambda x: float(x.price) if x.price.isdigit() else float('inf'))
        
        # Convert to dictionary format
        output_results = []
        for result in valid_results:
            output_results.append(asdict(result))
        
        # Save results to JSON file
        try:
            filename = f"{country}_{query.replace(' ', '_')}_results.json"
            with open(filename, "w", encoding='utf-8') as f:
                json.dump(output_results, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving results to file: {e}")
        
        logger.info(f"Found {len(output_results)} valid results")
        return output_results

def main():
    parser = argparse.ArgumentParser(description="Advanced Price Comparison Scraper by Sneha Jajodia")
    parser.add_argument("--country", required=True, help="Country code (US, IN, UK, CA)")
    parser.add_argument("--query", required=True, help="Product search query")
    parser.add_argument("--file", help="Optional JSON file with previously saved links to re-check")
    parser.add_argument("--headful", action="store_true", help="Run browser with UI (not headless)")
    parser.add_argument("--max-results", type=int, default=10, help="Maximum results per site")
    args = parser.parse_args()

    try:
        scraper = AdvancedPriceScraper()
        results = scraper.search_products(
            country=args.country.upper(),
            query=args.query,
            file_path=args.file,
            max_results_per_site=args.max_results,
            headless=not args.headful
        )
        
        print(f"\nFound {len(results)} results for '{args.query}' in {args.country.upper()}:\n")
        
        for i, r in enumerate(results[:10], 1):
            print(f"{i:2d}. {r['product_name'][:60]}...")
            print(f"    Price: {r['currency']} {r['price']} ({r['website']})")
            print(f"    Link: {r['link'][:80]}...\n")
            
        if len(results) > 10:
            print(f"... and {len(results) - 10} more results")
            
    except Exception as e:
        print(f"Error: {e}")
        print("\nTips:")
        print("- Try running with --headful to see the browser")
        print("- Use a residential IP address (home internet)")
        print("- Try different search terms")
        print("- Check the log file for detailed error information")

if __name__ == "__main__":
    main() 