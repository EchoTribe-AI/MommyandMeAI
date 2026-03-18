"""
EchoTribe Product API Integration
Handles Walmart, Amazon (via Crawlbase), and Impact affiliate link generation
"""

import os
import requests
import json
import hmac
import hashlib
import time
from typing import List, Dict, Optional
from urllib.parse import urlencode, quote


class WalmartAPI:
    """Walmart Product Catalog API integration"""
    
    BASE_URL = "https://developer.api.walmart.com/api-proxy/service/affil/product/v2"
    
    def __init__(self):
        self.public_key = os.environ.get('WALMART_API_PUBLIC_KEY')
        self.private_key = os.environ.get('WALMART_API_PRIVATE_KEY')
    
    def search(self, query: str, max_results: int = 3) -> List[Dict]:
        """Search Walmart products"""
        endpoint = f"{self.BASE_URL}/search"
        
        params = {
            'query': query,
            'numItems': max_results,
            'format': 'json'
        }
        
        headers = {
            'WM_SEC.KEY_VERSION': '1',
            'WM_CONSUMER.ID': self.public_key,
            'WM_SEC.AUTH_SIGNATURE': self._generate_signature(endpoint, params)
        }
        
        try:
            response = requests.get(endpoint, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            products = []
            for item in data.get('items', []):
                products.append({
                    'name': item.get('name', ''),
                    'price': f"${item.get('salePrice', 0):.2f}",
                    'was': f"${item.get('msrp', 0):.2f}" if item.get('msrp', 0) > item.get('salePrice', 0) else '',
                    'retailer': 'Walmart',
                    'sku': str(item.get('itemId', '')),
                    'url': item.get('productUrl', ''),
                    'image': item.get('largeImage', ''),
                    'category': item.get('categoryPath', '').split('/')[0] if item.get('categoryPath') else '',
                    'emoji': self._category_to_emoji(item.get('categoryPath', ''))
                })
            
            return products
            
        except requests.exceptions.RequestException as e:
            print(f"Walmart API error: {e}")
            return []
    
    def _generate_signature(self, url: str, params: Dict) -> str:
        """Generate HMAC signature for Walmart API authentication"""
        # Walmart uses timestamp-based HMAC signature
        timestamp = str(int(time.time() * 1000))
        
        # Build string to sign
        params_str = urlencode(sorted(params.items()))
        string_to_sign = f"{self.public_key}\n{url}\n{params_str}\n{timestamp}\n"
        
        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            self.private_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _category_to_emoji(self, category_path: str) -> str:
        """Map Walmart category to emoji"""
        category_lower = category_path.lower()
        
        if 'toy' in category_lower:
            return '🧸'
        elif 'baby' in category_lower:
            return '👶'
        elif 'home' in category_lower or 'furniture' in category_lower:
            return '🏠'
        elif 'beauty' in category_lower or 'health' in category_lower:
            return '💄'
        elif 'electronic' in category_lower:
            return '📱'
        elif 'cloth' in category_lower or 'fashion' in category_lower:
            return '👕'
        elif 'food' in category_lower or 'grocery' in category_lower:
            return '🍎'
        elif 'sport' in category_lower:
            return '⚽'
        else:
            return '🏪'


class CrawlbaseAPI:
    """Crawlbase API for Amazon product scraping"""
    
    BASE_URL = "https://api.crawlbase.com/"
    
    def __init__(self):
        self.token = os.environ.get('CRAWLBASE_JS_TOKEN')
    
    def search_amazon(self, query: str, max_results: int = 3) -> List[Dict]:
        """Search Amazon products via Crawlbase"""
        # Build Amazon search URL
        search_url = f"https://www.amazon.com/s?k={quote(query)}"
        
        params = {
            'token': self.token,
            'url': search_url,
            'ajax_wait': 'true',
            'page_wait': '2000'
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse HTML response to extract products
            products = self._parse_amazon_search(response.text, max_results)
            return products
            
        except requests.exceptions.RequestException as e:
            print(f"Crawlbase API error: {e}")
            return []
    
    def get_amazon_product(self, asin: str) -> Optional[Dict]:
        """Get detailed Amazon product info by ASIN"""
        product_url = f"https://www.amazon.com/dp/{asin}"
        
        params = {
            'token': self.token,
            'url': product_url,
            'ajax_wait': 'true',
            'page_wait': '2000'
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse product details
            product = self._parse_amazon_product(response.text, asin)
            return product
            
        except requests.exceptions.RequestException as e:
            print(f"Crawlbase product fetch error: {e}")
            return None
    
    def _parse_amazon_search(self, html: str, max_results: int) -> List[Dict]:
        """Parse Amazon search results HTML"""
        # This is a simplified parser - in production, use BeautifulSoup or similar
        products = []
        
        # TODO: Implement proper HTML parsing with BeautifulSoup
        # For now, return empty list - we'll use Hot Score catalog first
        
        return products
    
    def _parse_amazon_product(self, html: str, asin: str) -> Optional[Dict]:
        """Parse Amazon product page HTML"""
        # TODO: Implement proper HTML parsing with BeautifulSoup
        return None
    
    def build_affiliate_link(self, asin: str, tag: str = "mommymedeals-20") -> str:
        """Build Amazon affiliate link from ASIN"""
        return f"https://amazon.com/dp/{asin}?tag={tag}"


class ImpactAPI:
    """Impact.com API for Walmart affiliate link generation"""
    
    BASE_URL = "https://api.impact.com/Mediapartners"
    
    def __init__(self):
        self.account_sid = os.environ.get('IMPACT_ACCOUNT_SID')
        self.auth_token = os.environ.get('IMPACT_AUTH_TOKEN')
    
    def generate_walmart_link(self, product_url: str, product_id: str = None, 
                             sub_id1: str = "chat", sub_id2: str = None) -> str:
        """Generate Impact affiliate link for Walmart product"""
        
        # Impact API endpoint for link generation
        endpoint = f"{self.BASE_URL}/{self.account_sid}/Conversions/ConversionLink"
        
        # Walmart campaign ID (you'll need to get this from your Impact dashboard)
        campaign_id = "16662"  # This is from your example URL
        
        params = {
            'DestinationUrl': product_url,
            'CampaignId': campaign_id,
            'SubId1': sub_id1,
            'SubId2': sub_id2 or product_id or ''
        }
        
        auth = (self.account_sid, self.auth_token)
        
        try:
            response = requests.get(endpoint, params=params, auth=auth, timeout=10)
            response.raise_for_status()
            
            # Impact returns the tracking URL in the response
            data = response.json()
            
            # Look for vanity URL or tracking URL
            tracking_url = data.get('VanityUrl') or data.get('TrackingUrl')
            
            if tracking_url:
                return tracking_url
            else:
                # Fallback: build manual tracking URL
                return self._build_manual_link(product_url, product_id, sub_id1, sub_id2)
                
        except requests.exceptions.RequestException as e:
            print(f"Impact API error: {e}")
            # Fallback to manual link construction
            return self._build_manual_link(product_url, product_id, sub_id1, sub_id2)
    
    def _build_manual_link(self, product_url: str, product_id: str, 
                          sub_id1: str, sub_id2: str) -> str:
        """Build Impact tracking link manually"""
        # Based on your example structure:
        # https://goto.walmart.com/c/3590891/1398372/16662?veh=aff&u=URL&subId1=X&subId2=Y
        
        base = "https://goto.walmart.com/c/3590891/1398372/16662"
        encoded_url = quote(product_url, safe='')
        
        params = {
            'veh': 'aff',
            'u': encoded_url,
            'subId1': sub_id1,
            'subId2': sub_id2 or product_id or ''
        }
        
        return f"{base}?{urlencode(params)}"


class ProductResolver:
    """Smart product resolution with CVR-based routing"""
    
    # CVR routing rules from your docs
    CVR_RULES = {
        'toys': 'walmart',        # 16.7% CVR
        'baby': 'walmart',        # Same as toys
        'kids': 'walmart',        # Same as toys
        'beauty': 'ulta',         # $270 from Sol de Janeiro
        'skincare': 'ulta',
        'home': 'wayfair',        # Highest non-Walmart AOV
        'outdoor': 'wayfair',
        'shoes': 'footlocker',    # Kids Foot Locker
        'household': 'amazon',    # $80K Health & Household YTD
        'essentials': 'amazon',
        'grocery': 'amazon',      # #1 by units
        'food': 'amazon'
    }
    
    def __init__(self, hot_catalog: List[Dict]):
        self.hot_catalog = hot_catalog
        self.walmart_api = WalmartAPI()
        self.crawlbase_api = CrawlbaseAPI()
        self.impact_api = ImpactAPI()
    
    def resolve(self, query: str, category: str = None, max_results: int = 3) -> List[Dict]:
        """
        Resolve products for a query using intelligent routing:
        1. Search Hot Score catalog first
        2. If insufficient, search APIs based on CVR rules
        3. Generate affiliate links
        """
        results = []
        
        # Step 1: Search Hot Score catalog
        hot_matches = self._search_hot_catalog(query, category)
        results.extend(hot_matches)
        
        # Step 2: If we need more results, determine best retailer
        if len(results) < max_results:
            preferred_retailer = self._get_preferred_retailer(category)
            
            # Search based on preferred retailer
            if preferred_retailer == 'walmart':
                walmart_products = self.walmart_api.search(query, max_results - len(results))
                
                # Generate Impact affiliate links for Walmart products
                for product in walmart_products:
                    if product.get('url'):
                        product['link'] = self.impact_api.generate_walmart_link(
                            product['url'], 
                            product.get('sku'),
                            sub_id1='chat-recommendation',
                            sub_id2=product.get('sku')
                        )
                
                results.extend(walmart_products)
            
            elif preferred_retailer == 'amazon':
                # For now, fallback to Hot Score since Crawlbase needs HTML parsing
                # In production, implement full Crawlbase parsing
                pass
        
        # Step 3: Ensure all products have affiliate links
        for product in results:
            if not product.get('link'):
                if product['retailer'] == 'Amazon' and product.get('asin'):
                    product['link'] = self.crawlbase_api.build_affiliate_link(product['asin'])
                elif product['retailer'] == 'Walmart' and product.get('url'):
                    product['link'] = self.impact_api.generate_walmart_link(product['url'], product.get('sku'))
        
        return results[:max_results]
    
    def _search_hot_catalog(self, query: str, category: str = None) -> List[Dict]:
        """Search the Hot Score catalog"""
        query_lower = query.lower()
        matches = []
        
        for product in self.hot_catalog:
            # Check name match
            if any(word in product['name'].lower() for word in query_lower.split()):
                matches.append(product)
            # Check category match
            elif category and product.get('category') == category:
                matches.append(product)
        
        # Sort by Hot Score (highest first)
        matches.sort(key=lambda p: p.get('score', 0), reverse=True)
        
        return matches
    
    def _get_preferred_retailer(self, category: str = None) -> str:
        """Determine preferred retailer based on CVR rules"""
        if not category:
            return 'walmart'  # Default to Walmart (highest CVR overall)
        
        category_lower = category.lower() if category else ''
        
        # Check CVR rules
        for key, retailer in self.CVR_RULES.items():
            if key in category_lower:
                return retailer
        
        # Fallback to Walmart
        return 'walmart'


# Utility function to detect category from query
def detect_category(query: str) -> Optional[str]:
    """Detect product category from user query"""
    query_lower = query.lower()
    
    category_keywords = {
        'toys': ['toy', 'game', 'play', 'kid'],
        'baby': ['baby', 'infant', 'toddler', 'nursery'],
        'beauty': ['beauty', 'makeup', 'skincare', 'cosmetic'],
        'home': ['home', 'furniture', 'decor', 'kitchen'],
        'food': ['food', 'grocery', 'snack'],
        'clothing': ['cloth', 'dress', 'shirt', 'pants', 'shoe']
    }
    
    for category, keywords in category_keywords.items():
        if any(kw in query_lower for kw in keywords):
            return category
    
    return None
