import os
import json
import sqlite3
import requests as req
from flask import Flask, send_from_directory, request, jsonify, render_template
import anthropic
from product_api import ProductResolver, detect_category

app = Flask(__name__)

THEMES = {
    'coral':    {'bg': '#fff5f5', 'accent': '#ff6b6b', 'btn': '#e85d26', 'text': '#1a1a17'},
    'ocean':    {'bg': '#e8f4f8', 'accent': '#2e7dd4', 'btn': '#0a6b52', 'text': '#0f4a8a'},
    'lavender': {'bg': '#f5f0ff', 'accent': '#a78bfa', 'btn': '#ec4899', 'text': '#4c1d95'},
    'forest':   {'bg': '#f0f7f2', 'accent': '#27693a', 'btn': '#8a5510', 'text': '#1a2e1a'},
    'midnight': {'bg': '#1a1a17', 'accent': '#e8e5dc', 'btn': '#888780', 'text': '#e8e5dc'},
    'peach':    {'bg': '#fdf6f0', 'accent': '#e85d26', 'btn': '#8a5510', 'text': '#1a1a17'},
    'clean':    {'bg': '#ffffff', 'accent': '#1a1a17', 'btn': '#2e7dd4', 'text': '#1a1a17'},
    'bold':     {'bg': '#fff8f6', 'accent': '#e85d26', 'btn': '#a02828', 'text': '#1a1a17'},
}

PIXEL_ID = os.environ.get('FB_PIXEL_ID', '1559451780790812')

# Product catalog matching the frontend
PRODUCTS = [
    {'id': 0, 'name': 'Barbie Dreamhouse Pool Party 75+ Pieces', 'price': '$179', 'was': '$210', 'retailer': 'Amazon', 'emoji': '🏠', 'link': 'https://amazon.com/dp/B0C...?tag=mommymedeals-20'},
    {'id': 1, 'name': '2026 Glitter Dumpling Squishy Toy', 'price': '$13.49', 'was': '', 'retailer': 'Amazon', 'emoji': '✨', 'link': 'https://amazon.com/dp/B0D...?tag=mommymedeals-20'},
    {'id': 2, 'name': 'Ms. Rachel Toddler Hoodie + Jogger Set', 'price': '$7.00', 'was': '$15.98', 'retailer': 'Walmart', 'emoji': '🧸', 'link': 'https://goto.walmart.com/ZVboz1'},
    {'id': 3, 'name': 'Melissa & Doug Steering Wheel Dashboard', 'price': '$28', 'was': '', 'retailer': 'Amazon', 'emoji': '🚗', 'link': 'https://amazon.com/dp/B0A...?tag=mommymedeals-20'},
    {'id': 4, 'name': 'Stanley Quencher 40oz Tumbler', 'price': '$35', 'was': '$45', 'retailer': 'Amazon', 'emoji': '🥤', 'link': 'https://amazon.com/dp/B09...?tag=mommymedeals-20'},
    {'id': 5, 'name': 'Moana 2 Kids Underwear 7-Pack', 'price': '$10', 'was': '', 'retailer': 'Amazon', 'emoji': '🌊', 'link': 'https://amazon.com/dp/B0E...?tag=mommymedeals-20'},
    {'id': 6, 'name': 'Imaginext Jurassic World Dinosaur Set', 'price': '$35', 'was': '$49', 'retailer': 'Walmart', 'emoji': '🦕', 'link': 'https://goto.walmart.com/'},
    {'id': 7, 'name': 'Sol de Janeiro Travel Fragrance Set', 'price': '$32', 'was': '', 'retailer': 'Ulta', 'emoji': '🌸', 'link': 'https://www.ulta.com/...?PID=1390'},
    {'id': 8, 'name': 'Kinetic Sand Deluxe Gift Bag', 'price': '$14', 'was': '', 'retailer': 'Target', 'emoji': '⏳', 'link': 'https://target.com/'},
    {'id': 9, 'name': 'Keter Plastic Storage Box 55-Gallon', 'price': '$39', 'was': '$55', 'retailer': 'Wayfair', 'emoji': '📦', 'link': 'https://wayfair.com/'},
    {'id': 10, 'name': 'OXO Good Grips Silicone Utensil Set', 'price': '$18.99', 'was': '$24.99', 'retailer': 'Walmart', 'emoji': '🍳', 'link': 'https://goto.walmart.com/c/kitchen', 'category': 'home'},
    {'id': 11, 'name': 'Instant Pot Duo Crisp 8-Quart Pressure Cooker', 'price': '$99', 'was': '$149', 'retailer': 'Amazon', 'emoji': '🍲', 'link': 'https://amazon.com/dp/B08...?tag=mommymedeals-20', 'category': 'home'},
    {'id': 12, 'name': 'ChefJet 3-in-1 Vegetable Chopper', 'price': '$16.49', 'was': '$19.99', 'retailer': 'Walmart', 'emoji': '🥬', 'link': 'https://goto.walmart.com/c/kitchen', 'category': 'home'},
]

product_resolver = ProductResolver(PRODUCTS)

SYSTEM_PROMPT = """You are Steph, the creator behind @EverydaywithSteph and the Mommy & Me Collective. You talk mom-to-mom: warm, enthusiastic, concise, and occasionally use light emojis (but not excessively). You share deals and product recommendations like a trusted friend who happens to know every sale happening right now.

Your current top products and data:

PRODUCTS (index by ID for recommendations):
0. Barbie Dreamhouse Pool Party | $179 (was $210) | Amazon | 37,199 clicks | score 94 | category: toys
1. Glitter Dumpling Squishy 2026 | $13.49 | Amazon | 702 units sold | score 89 | category: toys
2. Ms. Rachel Toddler Set | $7.00 (was $15.98) | Walmart | 56% off clearance | score 82 | category: toys
3. Melissa & Doug Dashboard | $28 | Amazon | 262 clicks today | score 78 | category: toys
4. Stanley Quencher 40oz | $35 (was $45) | Amazon | 1,300 clicks | score 68 | category: beauty
5. Moana 2 Underwear 7-Pack | $10 | Amazon | 5,840 clicks | score 72 | category: baby
6. Imaginext Jurassic Dino Set | $35 (was $49) | Walmart | Walmart storefront pick | score 65 | category: toys
7. Sol de Janeiro Travel Set | $32 | Ulta | $270 earned, 42 orders | score 71 | category: beauty
8. Kinetic Sand Gift Bag | $14 | Target | 4,278 clicks | score 63 | category: toys
9. Keter Storage Box | $39 (was $55) | Wayfair | Top Wayfair earner | score 58 | category: home
10. OXO Good Grips Silicone Utensil Set | $18.99 (was $24.99) | Walmart | kitchen essentials | score 76 | category: home
11. Instant Pot Duo Crisp 8-Quart | $99 (was $149) | Amazon | 2,150 clicks | score 85 | category: home
12. ChefJet 3-in-1 Vegetable Chopper | $16.49 (was $19.99) | Walmart | meal prep helper | score 74 | category: home

KEY FACTS:
- Walmart converts at 16.7% — always route budget deals there first
- Toys & Games is your top Amazon category by clicks and revenue
- Barbie Dreamhouse has 37K clicks — your single highest-traffic product
- Your LTK storefront: shopltk.com/EverydaywithSteph

RESPONSE RULES:
- Keep replies to 2-4 sentences max
- Recommend specific products with prices when relevant
- If a budget deal exists at Walmart, mention Walmart first
- End with a helpful nudge when natural
- Never break character or mention Claude/AI

PRODUCT RECOMMENDATION FORMAT (CRITICAL - ALWAYS FOLLOW):
You MUST end EVERY response with either PRODUCTS: or SEARCH: line. Never end without one.

**Option 1: PRODUCTS format** (when you have exact matches in the catalog above)
End with: PRODUCTS: 0,1,2
Example:
User: "best toy under $30?"
Response: "oooh I have the PERFECT picks for you! The Ms. Rachel set is only $7 at Walmart right now (56% off 😱), or the Glitter Dumpling Squishy for $13.49 — my kids are OBSESSED with it. Both are total winners!
PRODUCTS: 2,1"

**Option 2: SEARCH format** (when user asks for something NOT in your catalog)
End with: SEARCH: category searchterm
Example:
User: "show me cheap kitchen gadgets"
Response: "Let me find you some amazing kitchen gadgets that won't break the bank!
SEARCH: home kitchen gadgets cheap"

User: "what about bluetooth speakers?"
Response: "Great question! Let me search for those!
SEARCH: electronics bluetooth speakers"

RULES:
- If your 10 Hot Score products match the user's request → use PRODUCTS: format
- If user asks for something OUTSIDE your catalog → ALWAYS use SEARCH: format
- Kitchen gadgets → NOT in catalog → use SEARCH:
- Bluetooth speakers → NOT in catalog → use SEARCH:
- Toys under $30 → IN catalog → use PRODUCTS:
- DO NOT respond without a final PRODUCTS: or SEARCH: line
- SEARCH: queries should be concise (2-3 keywords max)"""

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get('message') or '').strip()
    print(f"[CHAT] Received message: {user_message[:50]}...")
    if not user_message:
        return jsonify({'error': 'message is required'}), 400

    try:
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        message = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=256,
            system=SYSTEM_PROMPT,
            messages=[{'role': 'user', 'content': user_message}],
        )
        reply = message.content[0].text
        print(f"[REPLY] Claude response length: {len(reply)} | Contains PRODUCTS: {'PRODUCTS:' in reply} | Contains SEARCH: {'SEARCH:' in reply}")
        
        # Parse product recommendations from response
        products = []
        text_reply = reply
        
        if 'PRODUCTS:' in reply:
            parts = reply.split('PRODUCTS:')
            text_reply = parts[0].strip()
            product_ids_str = parts[1].strip()
            
            try:
                product_ids = [int(pid.strip()) for pid in product_ids_str.split(',')]
                products = [PRODUCTS[pid] for pid in product_ids if 0 <= pid < len(PRODUCTS)]
            except (ValueError, IndexError):
                pass
        
        elif 'SEARCH:' in reply:
            parts = reply.split('SEARCH:')
            text_reply = parts[0].strip()
            search_query = parts[1].strip()
            
            category = detect_category(search_query)
            
            try:
                resolved_products = product_resolver.resolve(search_query, category, max_results=3)
                products = resolved_products
            except Exception as e:
                products = []
        
        else:
            # Fallback: If Claude didn't include PRODUCTS: or SEARCH: but the query suggests searching,
            # detect and trigger search automatically
            # Common search indicators: "show me", "find", "cheap", "budget", "kitchen", "gadgets", "decor", etc.
            search_indicators = ['show me', 'find', 'search for', 'look for', 'what about', 'kitchen', 'gadget', 
                               'decor', 'furniture', 'cheap', 'budget', 'affordable', 'inexpensive', 'under $']
            
            has_search_indicator = any(indicator in user_message.lower() for indicator in search_indicators)
            print(f"[DEBUG] No PRODUCTS/SEARCH in reply. Has search indicator: {has_search_indicator}")
            
            if has_search_indicator:
                # User is likely asking for something to search for
                category = detect_category(user_message)
                print(f"[DEBUG] Detected category: {category}")
                try:
                    resolved_products = product_resolver.resolve(user_message, category, max_results=3)
                    products = resolved_products
                    print(f"🔍 Auto-triggered search for: {user_message} | Found {len(products)} products")
                except Exception as e:
                    print(f"[ERROR] Product resolution error: {e}")
                    import traceback
                    traceback.print_exc()
                    products = []
        
        return jsonify({
            'reply': text_reply,
            'products': products
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/plan')
def plan():
    return send_from_directory('.', 'steph-ai-plan.html')

@app.route('/architecture')
def architecture():
    return send_from_directory('.', 'steph-architecture.html')

@app.route('/connections')
def connections():
    return send_from_directory('.', 'steph-connection-map.html')

@app.route('/archer/products')
def archer_products():
    return render_template('archer_products.html')

@app.route('/archer/matched')
def archer_matched():
    """Return all 217 matched ASINs from the SQLite cache, merged with revenue data from JSON."""
    from product_api import ArcherAPI
    a = ArcherAPI()
    matched_json = a._load_matched_json()
    revenue_map = {p['asin']: p for p in matched_json}
    asins = [p['asin'] for p in matched_json]
    products = a.get_by_asins(asins)
    for p in products:
        asin = p.get('asin', '')
        if asin in revenue_map:
            p['steph_revenue'] = revenue_map[asin].get('steph_revenue', 0)
            p['steph_units'] = revenue_map[asin].get('steph_units', 0)
    if not products:
        products = matched_json
    return jsonify({'products': products})

@app.route('/archer/search')
def archer_search():
    """Search the Archer catalog SQLite cache."""
    from product_api import ArcherAPI
    q = request.args.get('q', '')
    category = request.args.get('category', '')
    min_commission = int(request.args.get('min_commission', 0))
    limit = int(request.args.get('limit', 24))
    a = ArcherAPI()
    results = a.search_catalog(q, category=category or None, limit=limit)
    if min_commission > 0:
        results = [p for p in results if float((p.get('commission_payout') or '0').replace('%', '') or 0) >= min_commission]
    return jsonify({'products': results})

@app.route('/archer/backfill_images')
def archer_backfill_images():
    """One-time route to populate image URLs for matched ASINs."""
    from product_api import ArcherAPI
    a = ArcherAPI()
    matched = a._load_matched_json()
    asins = [p['asin'] for p in matched]
    updated = a.backfill_images(asins)
    return jsonify({'updated': updated, 'total': len(asins)})

@app.route('/archer/generate_link', methods=['POST'])
def archer_generate_link():
    """Generate a live Archer attribution link for a given ASIN."""
    from product_api import ArcherAPI
    data = request.get_json() or {}
    asin = data.get('asin', '').strip()
    label = data.get('label', asin)
    if not asin:
        return jsonify({'error': 'asin is required'}), 400
    a = ArcherAPI()
    result = a.generate_link(asin, label=label)
    if not result:
        return jsonify({'error': 'Link generation failed'}), 500
    return jsonify(result)

@app.route('/archer/collage')
def archer_collage():
    return render_template('archer_collage.html')

@app.route('/archer/product/<asin>')
def archer_get_product(asin):
    from product_api import ArcherAPI
    import logging
    a = ArcherAPI()
    product = a.get_by_asins([asin])

    # If found in cache but no image, force a live lookup to backfill
    if product and not product[0].get('image_encoded_string'):
        product = []

    if not product:
        try:
            r = req.get('https://api.archeraffiliates.com/get_single_product',
                headers={"Authorization": f"Bearer {a._get_token()}"},
                params={"asin": asin}, timeout=10)
            if r.status_code == 200:
                data = r.json()
                img = data.get("image_encoded_string", "")
                if img:
                    conn = sqlite3.connect(a.CACHE_DB)
                    conn.execute("UPDATE products SET image_encoded_string=? WHERE asin=?", (img, asin))
                    conn.commit()
                    conn.close()
                return jsonify({"product": {
                    "asin": data.get("ASIN"),
                    "product_name": data.get("product_name"),
                    "company_name": data.get("company_name"),
                    "price": data.get("price"),
                    "commission_payout": data.get("commission_payout_aff"),
                    "image_encoded_string": img,
                    "product_category": data.get("product_category")
                }})
        except Exception as e:
            logging.error(f"[ARCHER] Product lookup failed for {asin}: {e}")
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"product": product[0]})

@app.route('/archer/generate_caption', methods=['POST'])
def archer_generate_caption():
    data = request.get_json() or {}
    products_str = data.get('products', '')
    try:
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        message = client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=200,
            system="""You are Steph from @EverydaywithSteph and the Mommy & Me Collective.
Write a short, enthusiastic Facebook/Instagram caption for a product collage.
Keep it 2-3 sentences max. Warm, mom-to-mom tone. Light emojis.
Mention the products naturally. End with a call to action like "Links in bio!" or "Shop below! 👇"
Return ONLY the caption text, nothing else.""",
            messages=[{"role": "user", "content": f"Write a caption for these products: {products_str}"}]
        )
        return jsonify({"caption": message.content[0].text.strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/archer/collage/save', methods=['POST'])
def archer_save_collage():
    from product_api import ArcherAPI
    data = request.get_json() or {}
    slug = data.get('slug', '').strip().lower().replace(' ', '-')
    if not slug or not data.get('products'):
        return jsonify({'error': 'slug and products required'}), 400

    a = ArcherAPI()
    products = data.get('products', [])
    for p in products:
        asin = p.get('asin', '')
        if asin and not p.get('attribution_link'):
            link = a.generate_link(asin, label=f"{slug}-{asin.lower()}")
            if link:
                p['attribution_link'] = link.get('attribution_link') or link.get('url') or ''

    conn = sqlite3.connect(a.CACHE_DB)
    conn.execute("""
        INSERT OR REPLACE INTO collages
        (slug, products_json, layout, theme, caption, direct_to_amazon, created_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        slug,
        json.dumps(products),
        data.get('layout', 'layout-2'),
        data.get('theme', 'coral'),
        data.get('caption', ''),
        1 if data.get('direct_to_amazon') else 0
    ))
    conn.commit()
    conn.close()
    return jsonify({'url': f'/shop/{slug}', 'slug': slug})

@app.route('/archer/collages')
def archer_list_collages():
    from product_api import ArcherAPI
    a = ArcherAPI()
    conn = sqlite3.connect(a.CACHE_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT slug, theme, layout, created_at, click_count, products_json FROM collages ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    conn.close()
    collages = []
    for r in rows:
        products = json.loads(r['products_json'] or '[]')
        collages.append({
            'slug': r['slug'],
            'theme': r['theme'],
            'layout': r['layout'],
            'created_at': r['created_at'][:10] if r['created_at'] else '',
            'click_count': r['click_count'] or 0,
            'product_count': len(products)
        })
    return jsonify({'collages': collages})

@app.route('/shop/<slug>')
def shop_landing(slug):
    from product_api import ArcherAPI
    a = ArcherAPI()
    conn = sqlite3.connect(a.CACHE_DB)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM collages WHERE slug=?", (slug,)).fetchone()
    conn.close()
    if not row:
        return "Page not found", 404
    collage = dict(row)
    products = json.loads(collage.get('products_json') or '[]')
    collage['direct_to_amazon'] = bool(collage.get('direct_to_amazon'))
    return render_template('shop_landing.html',
        collage=collage,
        products=products,
        themes=THEMES,
        pixel_id=PIXEL_ID
    )

@app.route('/archer/track_click', methods=['POST'])
def archer_track_click():
    from product_api import ArcherAPI
    data = request.get_json() or {}
    a = ArcherAPI()
    conn = sqlite3.connect(a.CACHE_DB)
    conn.execute(
        "INSERT INTO click_log (asin, slug, fbclid, attribution_url) VALUES (?,?,?,?)",
        (data.get('asin'), data.get('slug'), data.get('fbclid'), data.get('attribution_url'))
    )
    conn.execute(
        "UPDATE collages SET click_count = click_count + 1 WHERE slug=?",
        (data.get('slug'),)
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')
