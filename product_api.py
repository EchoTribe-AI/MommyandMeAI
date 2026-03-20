"""
EchoTribe Product API Integration
Handles Walmart, Amazon (via Crawlbase), Impact affiliate link generation, and Archer Affiliates
"""

import os
import requests
import json
import hmac
import hashlib
import logging
import sqlite3
import time
from datetime import datetime, timedelta
import time
import base64
import uuid
from typing import List, Dict, Optional
from urllib.parse import urlencode, quote


class WalmartAPI:
    """Walmart Affiliate Product API integration with RSA-SHA256 authentication"""
    
    BASE_URL = "https://developer.api.walmart.com"
    
    def __init__(self):
        self.consumer_id = os.environ.get('WALMART_API_PUBLIC_KEY')
        raw_key = os.environ.get('WALMART_API_PRIVATE_KEY') or ""
        # Fix: Replace escaped newlines (\n as two chars) with actual newlines
        self.private_key_pem = raw_key.replace("\\n", "\n")
        self.publisher_id = os.environ.get('WALMART_PUBLISHER_ID') or self.consumer_id
    
    def search(self, query: str, max_results: int = 3) -> List[Dict]:
        """Search Walmart products with RSA-SHA256 authentication"""
        endpoint = f"{self.BASE_URL}/api-proxy/service/affil/product/v2/search"
        
        params = {
            'query': query,
            'numItems': max_results,
            'format': 'json',
            'publisherId': self.publisher_id
        }
        
        try:
            headers = self._build_headers(endpoint, params)
            if not headers:
                return []
            
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
            return []
        except Exception as e:
            return []
    
    def _build_headers(self, endpoint: str, params: Dict) -> Dict:
        """Build RSA-signed headers for Walmart Affiliate API"""
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.backends import default_backend
            import sys
            
            # Timestamp in milliseconds
            ts = str(int(time.time() * 1000))
            
            # Exact string to sign format: consumerId\ntimestamp\nkeyVersion\n
            string_to_sign = f"{self.consumer_id}\n{ts}\n1\n"
            
            # Load private key
            private_key = serialization.load_pem_private_key(
                self.private_key_pem.encode("utf-8"),
                password=None,
                backend=default_backend()
            )
            
            # Sign with PKCS1v15 + SHA256
            sig_bytes = private_key.sign(
                string_to_sign.encode("utf-8"),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            
            # Base64 encode the signature
            signature = base64.b64encode(sig_bytes).decode("utf-8")
            
            # Build all 6 required headers
            headers = {
                "WM_CONSUMER.ID": self.consumer_id,
                "WM_CONSUMER.INTIMESTAMP": ts,
                "WM_SEC.KEY_VERSION": "1",
                "WM_SEC.AUTH_SIGNATURE": signature,
                "WM_CONSUMER.CHANNEL.TYPE": "AFFILIATE",
                "WM_QOS.CORRELATION_ID": str(uuid.uuid4()),
                "Accept": "application/json"
            }
            
            return headers
        except Exception as e:
            return {}
    
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
            product = self._parse_amazon_product(response.text, asin)
            return product
            
        except requests.exceptions.RequestException as e:
            print(f"Crawlbase product fetch error: {e}")
            return None
    
    def _parse_amazon_search(self, html: str, max_results: int) -> List[Dict]:
        """Parse Amazon search results HTML"""
        products = []
        return products
    
    def _parse_amazon_product(self, html: str, asin: str) -> Optional[Dict]:
        """Parse Amazon product page HTML"""
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
        
        endpoint = f"{self.BASE_URL}/{self.account_sid}/Conversions/ConversionLink"
        campaign_id = "16662"
        
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
            data = response.json()
            tracking_url = data.get('VanityUrl') or data.get('TrackingUrl')
            
            if tracking_url:
                return tracking_url
            else:
                return self._build_manual_link(product_url, product_id, sub_id1, sub_id2)
                
        except requests.exceptions.RequestException as e:
            print(f"Impact API error: {e}")
            return self._build_manual_link(product_url, product_id, sub_id1, sub_id2)
    
    def _build_manual_link(self, product_url: str, product_id: str, 
                          sub_id1: str, sub_id2: str) -> str:
        """Build Impact tracking link manually"""
        base = "https://goto.walmart.com/c/3590891/1398372/16662"
        encoded_url = quote(product_url, safe='')
        
        params = {
            'veh': 'aff',
            'u': encoded_url,
            'subId1': sub_id1,
            'subId2': sub_id2 or product_id or ''
        }
        
        return f"{base}?{urlencode(params)}"


def detect_category(query: str) -> str:
    """Detect product category from search query"""
    query_lower = query.lower()

    category_keywords = {
        'toys': ['toy', 'doll', 'action figure', 'lego', 'playset', 'puzzle', 'game'],
        'baby': ['baby', 'infant', 'newborn', 'nursery', 'stroller'],
        'kids': ['kid', 'children', 'toddler', 'preschool'],
        'beauty': ['beauty', 'makeup', 'skincare', 'fragrance', 'cosmetic', 'serum', 'moisturizer'],
        'health': ['vitamin', 'supplement', 'protein', 'wellness', 'health', 'fitness'],
        'home': ['home', 'furniture', 'decor', 'kitchen', 'bedroom', 'appliance', 'gadget'],
        'outdoor': ['outdoor', 'garden', 'patio', 'camping', 'lawn'],
        'pets': ['pet', 'dog', 'cat', 'puppy', 'kitten'],
        'electronics': ['electronic', 'bluetooth', 'speaker', 'headphone', 'phone', 'tablet'],
        'clothing': ['clothing', 'shirt', 'pants', 'dress', 'shoes', 'jacket', 'fashion'],
        'grocery': ['food', 'snack', 'grocery', 'drink', 'coffee', 'tea'],
    }

    for category, keywords in category_keywords.items():
        if any(kw in query_lower for kw in keywords):
            return category

    return 'general'


class ArcherAPI:
    """Archer Affiliates API client with auto-refreshing bearer token and local SQLite catalog cache."""

    ARCHER_BASE = "https://api.archeraffiliates.com"
    CACHE_DB = "data/archer_catalog.db"
    CACHE_TTL_HOURS = 24
    MATCHED_ASINS_PATH = "data/matched_asins.json"

    def __init__(self):
        self.token = None
        self.token_expires = None
        self._init_cache()
        self._seed_from_json()

    # ── AUTH ──────────────────────────────────────────────

    def _get_token(self):
        if self.token and datetime.now() < self.token_expires:
            return self.token
        r = requests.post(f"{self.ARCHER_BASE}/token", data={
            "username": os.environ.get("ARCHER_USERNAME"),
            "password": os.environ.get("ARCHER_PASSWORD")
        })
        r.raise_for_status()
        self.token = r.json()["access_token"]
        self.token_expires = datetime.now() + timedelta(minutes=55)
        logging.info("[ARCHER] Token refreshed")
        return self.token

    def _headers(self):
        return {"Authorization": f"Bearer {self._get_token()}"}

    # ── CATALOG CACHE ─────────────────────────────────────

    def _init_cache(self):
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect(self.CACHE_DB)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                asin TEXT PRIMARY KEY,
                brand_id TEXT,
                company_name TEXT,
                product_name TEXT,
                price TEXT,
                commission_payout TEXT,
                product_category TEXT,
                sub_category TEXT,
                avg_rating TEXT,
                total_reviews TEXT,
                image_encoded_string TEXT,
                deal_json TEXT,
                product_status TEXT,
                steph_revenue REAL,
                steph_units INTEGER,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache_meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS collages (
                slug TEXT PRIMARY KEY,
                products_json TEXT,
                layout TEXT DEFAULT 'layout-2',
                theme TEXT DEFAULT 'coral',
                caption TEXT,
                direct_to_amazon INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                click_count INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS click_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT,
                slug TEXT,
                fbclid TEXT,
                attribution_url TEXT,
                clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                slug TEXT PRIMARY KEY,
                campaign_type TEXT DEFAULT 'organic',
                routing TEXT DEFAULT 'landing',
                products_json TEXT,
                variants_json TEXT,
                spend_budget REAL DEFAULT 0,
                forecast_roas TEXT,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def _seed_from_json(self):
        """Seed SQLite from matched_asins.json if DB is empty."""
        if not os.path.exists(self.MATCHED_ASINS_PATH):
            return
        conn = sqlite3.connect(self.CACHE_DB)
        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count > 0:
            conn.close()
            return
        try:
            with open(self.MATCHED_ASINS_PATH) as f:
                products = json.load(f)
            for p in products:
                conn.execute("""
                    INSERT OR IGNORE INTO products
                    (asin, company_name, product_name, price, commission_payout,
                     product_category, avg_rating, total_reviews, product_status,
                     steph_revenue, steph_units, cached_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
                """, (
                    p.get("asin"), p.get("brand"), p.get("product_name"),
                    p.get("price"), p.get("commission"),
                    p.get("archer_category"), p.get("rating"), p.get("reviews"),
                    "active", p.get("steph_revenue", 0), p.get("steph_units", 0)
                ))
            conn.commit()
            logging.info(f"[ARCHER] Seeded {len(products)} products from matched_asins.json")
        except Exception as e:
            logging.error(f"[ARCHER] Seed from JSON failed: {e}")
        finally:
            conn.close()

    def _cache_is_fresh(self):
        conn = sqlite3.connect(self.CACHE_DB)
        row = conn.execute(
            "SELECT value FROM cache_meta WHERE key='last_full_sync'"
        ).fetchone()
        conn.close()
        if not row:
            return False
        last_sync = datetime.fromisoformat(row[0])
        return datetime.now() - last_sync < timedelta(hours=self.CACHE_TTL_HOURS)

    def sync_catalog(self, force=False):
        """Pull full Archer catalog into SQLite. Skips if cache is fresh unless forced."""
        if not force and self._cache_is_fresh():
            logging.info("[ARCHER] Catalog cache is fresh, skipping sync")
            return

        logging.info("[ARCHER] Starting full catalog sync...")
        page, limit, total_synced = 1, 100, 0
        conn = sqlite3.connect(self.CACHE_DB)

        while True:
            try:
                r = requests.get(f"{self.ARCHER_BASE}/getproducts",
                    headers=self._headers(),
                    params={"page": page, "limit": limit},
                    timeout=30)
                r.raise_for_status()
                data = r.json()
                products = data.get("product_catalog", [])

                if not products:
                    break

                for p in products:
                    conn.execute("""
                        INSERT OR REPLACE INTO products
                        (asin, brand_id, company_name, product_name, price,
                         commission_payout, product_category, sub_category,
                         avg_rating, total_reviews, image_encoded_string,
                         deal_json, product_status, cached_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
                    """, (
                        p.get("ASIN"), p.get("brand_id"), p.get("company_name"),
                        p.get("product_name"), p.get("price"),
                        p.get("commission_payout_aff"), p.get("product_category"),
                        json.dumps(p.get("sub_category", [])),
                        p.get("avg_rating"), p.get("total_reviews"),
                        p.get("image_encoded_string"),
                        json.dumps(p.get("deal", {})),
                        p.get("product_status", "active")
                    ))

                total_synced += len(products)
                logging.info(f"[ARCHER] Synced page {page}, total: {total_synced}")

                if len(products) < limit:
                    break
                page += 1
                time.sleep(0.3)

            except Exception as e:
                logging.error(f"[ARCHER] Catalog sync error on page {page}: {e}")
                break

        conn.execute(
            "INSERT OR REPLACE INTO cache_meta (key, value) VALUES ('last_full_sync', ?)",
            (datetime.now().isoformat(),)
        )
        conn.commit()
        conn.close()
        logging.info(f"[ARCHER] Catalog sync complete. Total products: {total_synced}")

    # ── SEARCH ────────────────────────────────────────────

    def search_catalog(self, query, category=None, limit=5):
        """Search local SQLite cache, prioritizing Steph's highest-revenue products."""
        conn = sqlite3.connect(self.CACHE_DB)
        conn.row_factory = sqlite3.Row

        sql = """
            SELECT * FROM products
            WHERE product_status = 'active'
            AND (
                product_name LIKE ?
                OR company_name LIKE ?
                OR product_category LIKE ?
            )
        """
        params = [f"%{query}%", f"%{query}%", f"%{query}%"]

        if category:
            sql += " AND product_category LIKE ?"
            params.append(f"%{category}%")

        sql += " ORDER BY steph_revenue DESC, CAST(REPLACE(commission_payout, '%', '') AS REAL) DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def backfill_images(self, asins):
        """Fetch live product data for a list of ASINs and update image URLs in cache."""
        conn = sqlite3.connect(self.CACHE_DB)
        updated = 0
        for asin in asins:
            try:
                r = requests.get(f"{self.ARCHER_BASE}/get_single_product",
                    headers=self._headers(),
                    params={"asin": asin},
                    timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    img = data.get("image_encoded_string", "")
                    if img:
                        conn.execute(
                            "UPDATE products SET image_encoded_string=? WHERE asin=?",
                            (img, asin)
                        )
                        updated += 1
                time.sleep(0.2)
            except Exception as e:
                logging.warning(f"[ARCHER] Image backfill failed for {asin}: {e}")
        conn.commit()
        conn.close()
        logging.info(f"[ARCHER] Image backfill complete: {updated}/{len(asins)} updated")
        return updated

    def _load_matched_json(self):
        """Load matched_asins.json as a list of dicts."""
        try:
            with open(self.MATCHED_ASINS_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            return []

    def get_by_asin(self, asin):
        conn = sqlite3.connect(self.CACHE_DB)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM products WHERE asin = ?", (asin,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def get_by_asins(self, asin_list):
        if not asin_list:
            return []
        conn = sqlite3.connect(self.CACHE_DB)
        conn.row_factory = sqlite3.Row
        placeholders = ",".join("?" * len(asin_list))
        rows = conn.execute(
            f"SELECT * FROM products WHERE asin IN ({placeholders}) AND product_status='active'",
            asin_list
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ── LINK GENERATION ──────────────────────────────────

    def generate_link(self, asin, label=None):
        """Generate a tracked Archer attribution link for a given ASIN."""
        try:
            r = requests.post(f"{self.ARCHER_BASE}/generate_attribution_link",
                headers=self._headers(),
                json={"asin": asin, "link_name": label or asin},
                timeout=10)
            r.raise_for_status()
            data = r.json()
            logging.info(f"[ARCHER] Generated link for ASIN {asin}")
            return data
        except Exception as e:
            logging.error(f"[ARCHER] Link generation failed for {asin}: {e}")
            return None

    # ── REPORTING ─────────────────────────────────────────

    def get_insights(self, start_date, end_date, asin=None, category=None, brand=None, page=1):
        """Pull product-level insights. Dates in YYYYMMDD format."""
        params = {"start_date": start_date, "end_date": end_date, "page": page, "limit": 100}
        if asin: params["productAsin"] = asin
        if category: params["productCategory"] = category
        if brand: params["brand"] = brand
        r = requests.get(f"{self.ARCHER_BASE}/insights",
            headers=self._headers(), params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def get_affiliate_id(self):
        r = requests.get(f"{self.ARCHER_BASE}/get_affiliateID", headers=self._headers())
        r.raise_for_status()
        return r.json()

    # ── PRODUCT FORMAT HELPER ─────────────────────────────

    def format_for_frontend(self, archer_product, attribution_url=None):
        """Convert Archer catalog product to the frontend product dict format."""
        deal = {}
        try:
            deal = json.loads(archer_product.get("deal_json") or "{}")
        except Exception:
            pass

        price = archer_product.get("price", "")
        sale_price = deal.get("sale_price")
        final_price = deal.get("final_price")
        display_price = f"${final_price}" if final_price else (f"${sale_price}" if sale_price else price)
        was_price = f"${deal.get('base_price')}" if deal.get("base_price") and deal.get("final_discount_%") else ""

        asin = archer_product.get("asin")
        return {
            "id": asin,
            "name": archer_product.get("product_name", ""),
            "price": display_price,
            "was": was_price,
            "retailer": "Amazon",
            "emoji": "🏹",
            "link": attribution_url or f"https://amazon.com/dp/{asin}",
            "asin": asin,
            "brand": archer_product.get("company_name", ""),
            "category": archer_product.get("product_category", ""),
            "commission": archer_product.get("commission_payout", ""),
            "rating": archer_product.get("avg_rating", ""),
            "reviews": archer_product.get("total_reviews", ""),
            "deal": deal,
            "source": "archer"
        }


# Singleton — import this everywhere
archer_api = ArcherAPI()


class ProductResolver:
    """Smart product resolution with CVR-based routing"""

    CVR_RULES = {
        'toys': 'walmart',
        'baby': 'walmart',
        'kids': 'walmart',
        'beauty': 'archer',
        'health': 'archer',
        'skincare': 'archer',
        'electronics': 'archer',
        'clothing': 'archer',
        'pets': 'archer',
        'home': 'archer',
        'outdoor': 'wayfair',
        'household': 'amazon',
        'essentials': 'amazon',
        'grocery': 'amazon',
        'food': 'amazon'
    }

    def __init__(self, hot_catalog: List[Dict]):
        self.hot_catalog = hot_catalog
        self.walmart_api = WalmartAPI()
        self.crawlbase_api = CrawlbaseAPI()
        self.impact_api = ImpactAPI()
        self.archer_api = archer_api

    def resolve(self, query: str, category: str = None, max_results: int = 3) -> List[Dict]:
        """
        Resolve products for a query using intelligent routing:
        1. Search Hot Score catalog first
        2. Search Archer catalog (matched ASINs with attribution links)
        3. Fall back to Walmart API
        4. Generate affiliate links for any unlinked results
        """
        results = []

        # Step 1: Hot Score catalog
        hot_matches = self._search_hot_catalog(query, category)
        results.extend(hot_matches)

        # Step 2: Archer catalog
        if len(results) < max_results:
            try:
                archer_matches = self.archer_api.search_catalog(
                    query, category, limit=max_results - len(results)
                )
                for p in archer_matches:
                    link_data = self.archer_api.generate_link(
                        p['asin'], label=f"chat-{category or 'general'}"
                    )
                    url = link_data.get('url') if link_data else None
                    results.append(self.archer_api.format_for_frontend(p, url))
            except Exception as e:
                logging.error(f"[ARCHER] Resolution error: {e}")

        # Step 3: Walmart API fallback
        if len(results) < max_results:
            preferred_retailer = self._get_preferred_retailer(category)

            if preferred_retailer == 'walmart':
                walmart_products = self.walmart_api.search(query, max_results - len(results))
                for product in walmart_products:
                    if product.get('url'):
                        product['link'] = self.impact_api.generate_walmart_link(
                            product['url'], product.get('sku'),
                            sub_id1='chat-recommendation', sub_id2=product.get('sku')
                        )
                results.extend(walmart_products)
            else:
                walmart_products = self.walmart_api.search(query, max_results - len(results))
                if walmart_products:
                    for product in walmart_products:
                        if product.get('url'):
                            product['link'] = self.impact_api.generate_walmart_link(
                                product['url'], product.get('sku'),
                                sub_id1='chat-recommendation', sub_id2=product.get('sku')
                            )
                    results.extend(walmart_products)
                else:
                    hot_fallback = self._search_hot_catalog(query, category)
                    results.extend(hot_fallback[:max_results - len(results)])

        # Fill any missing links
        for product in results:
            if not product.get('link'):
                if product.get('retailer') == 'Amazon' and product.get('asin'):
                    product['link'] = self.crawlbase_api.build_affiliate_link(product['asin'])
                elif product.get('retailer') == 'Walmart' and product.get('url'):
                    product['link'] = self.impact_api.generate_walmart_link(product['url'], product.get('sku'))

        return results[:max_results]

    def _search_hot_catalog(self, query: str, category: str = None) -> List[Dict]:
        """Search the Hot Score catalog with improved matching"""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        matches = []

        for product in self.hot_catalog:
            score = 0

            if any(word in product['name'].lower() for word in query_words if len(word) > 2):
                score += 3

            if category and category.lower() in product.get('category', '').lower():
                score += 2
            elif any(word in product.get('category', '').lower() for word in query_words):
                score += 1

            if score > 0:
                matches.append((score, product))

        matches.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in matches]

    def _get_preferred_retailer(self, category: str) -> str:
        if not category:
            return 'walmart'
        return self.CVR_RULES.get(category, 'walmart')
