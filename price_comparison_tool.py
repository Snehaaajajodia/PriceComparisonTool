#!/usr/bin/env python3
"""
Advanced Price Comparison Tool with CLI
Created by: Sneha Jajodia
"""

from playwright.sync_api import sync_playwright
import time
import random
import re
import json
import argparse
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
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

class PriceComparisonTool:
    """Main price comparison tool class"""
    
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
        ]
        
        self.locales = ['en-US', 'en-IN', 'hi-IN', 'en-GB']
        
        # Website configurations for different countries
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
                "reliancedigital": {
                    "base_url": "https://www.reliancedigital.in",
                    "search_url": "https://www.reliancedigital.in/search?q={query}",
                    "selectors": {
                        "product_container": "div.sp__product",
                        "product_name": "a.sp__product__title",
                        "price": "span[data-bind*='price']",
                        "currency": "INR",
                        "link": "a.sp__product__title"
                    }
                },
                "vijaysales": {
                    "base_url": "https://www.vijaysales.com",
                    "search_url": "https://www.vijaysales.com/search/{query}",
                    "selectors": {
                        "product_container": "div.productMainBox",
                        "product_name": "h3.productMainName a",
                        "price": "span.offerprice",
                        "currency": "INR",
                        "link": "h3.productMainName a"
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
    
    def detect_captcha(self, page) -> bool:
        """Detect if page contains CAPTCHA"""
        try:
            html = page.content().lower()
            captcha_indicators = [
                "captcha", "verify you are human", "robot check", 
                "security check", "please verify", "prove you're not a robot",
                "enter the characters you see below"
            ]
            
            for indicator in captcha_indicators:
                if indicator in html:
                    logger.warning(f"Detected CAPTCHA page with indicator: {indicator}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error detecting CAPTCHA: {e}")
            return False
    
    def simulate_human_behavior(self, page):
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
    
    def search_website(self, config, query, max_results=10, headless=True) -> List[ProductResult]:
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
                        "--disable-javascript",  # Sometimes helps with detection
                    ]
                )
                
                # Create context with enhanced stealth settings
                context = browser.new_context(
                    user_agent=random.choice(self.user_agents),
                    viewport={'width': random.randint(1200, 1800), 'height': random.randint(800, 1200)},
                    java_script_enabled=True,
                    locale=random.choice(self.locales),
                    timezone_id='Asia/Kolkata' if 'IN' in config['base_url'] else 'America/New_York',
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
                
                page = context.new_page()
                
                # Navigate to search page with increased timeout
                search_url = config["search_url"].format(query=query.replace(' ', '+'))
                logger.info(f"Navigating to: {search_url}")
                
                page.goto(search_url, timeout=60000, wait_until='domcontentloaded')
                
                # Wait for content to load
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
                
                # Debug: Check if we can find any elements with the selectors
                if len(containers) == 0:
                    logger.warning(f"No containers found with selector: {selectors['product_container']}")
                    # Try to find any elements that might be products
                    all_divs = page.query_selector_all("div")
                    logger.info(f"Total divs on page: {len(all_divs)}")
                    
                    # Try alternative selectors
                    alt_containers = page.query_selector_all("[data-component-type*='search']")
                    logger.info(f"Alternative containers found: {len(alt_containers)}")
                    
                    if len(alt_containers) > 0:
                        containers = alt_containers
                
                for container in containers[:max_results]:
                    try:
                        # Extract product name - try multiple selectors
                        product_name = ""
                        name_selectors = selectors["product_name"].split(", ")
                        for name_selector in name_selectors:
                            name_elem = container.query_selector(name_selector.strip())
                            if name_elem:
                                product_name = name_elem.inner_text().strip()
                                break
                        
                        if not product_name:
                            continue
                        
                        # Extract price - try multiple selectors
                        price = "0"
                        price_selectors = selectors["price"].split(", ")
                        for price_selector in price_selectors:
                            price_elem = container.query_selector(price_selector.strip())
                            if price_elem:
                                price_text = price_elem.inner_text().strip()
                                extracted_price = self.extract_price(price_text)
                                if extracted_price != "0":
                                    price = extracted_price
                                    break
                        
                        # Extract link - try multiple selectors
                        link = ""
                        link_selectors = selectors["link"].split(", ")
                        for link_selector in link_selectors:
                            link_elem = container.query_selector(link_selector.strip())
                            if link_elem:
                                href = link_elem.get_attribute("href")
                                if href:
                                    link = f"{config['base_url']}{href}" if href.startswith('/') else href
                                    break
                        
                        if not link:
                            continue
                        
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
    
    def search_products(self, country, query, max_results_per_site=10, headless=True) -> List[Dict]:
        """Main search function with enhanced features"""
        logger.info(f"🔍 Searching for '{query}' in {country}")
        
        if country not in self.website_configs:
            raise ValueError(f"Country {country} not supported")
        
        all_results = []
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
            output_results.append({
                "link": result.link,
                "price": result.price,
                "currency": result.currency,
                "product_name": result.product_name,
                "website": result.website
            })
        
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
    parser = argparse.ArgumentParser(description="Price Comparison Tool by Sneha Jajodia")
    parser.add_argument("--country", required=True, help="Country code (US, IN)")
    parser.add_argument("--query", required=True, help="Product search query")
    parser.add_argument("--headful", action="store_true", help="Run browser with UI (not headless)")
    parser.add_argument("--max-results", type=int, default=10, help="Maximum results per site")
    args = parser.parse_args()

    try:
        tool = PriceComparisonTool()
        results = tool.search_products(
            country=args.country.upper(),
            query=args.query,
            max_results_per_site=args.max_results,
            headless=not args.headful
        )
        print(f"\n✅ Found {len(results)} results for '{args.query}' in {args.country.upper()}:\n")
        for i, r in enumerate(results[:10], 1):
            print(f"{i:2d}. {r['product_name'][:60]}...")
            print(f"    Price: {r['currency']} {r['price']} ({r['website']})")
            print(f"    Link: {r['link'][:80]}...\n")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Tips:")
        print("- Try running with --headful to see the browser")
        print("- Use a residential IP address (home internet)")
        print("- Try different search terms")

if __name__ == "__main__":
    main() 