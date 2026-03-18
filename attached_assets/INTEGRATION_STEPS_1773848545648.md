# API Integration Steps for MommyandMeAI Repo

## ✅ Current Status (What's Already Working)

Your repo already has:
- ✅ Product cards UI (CSS + JavaScript rendering)
- ✅ Backend product parsing (PRODUCTS array + ID parsing)
- ✅ Chat endpoint returning products
- ✅ Flask routes for all pages
- ✅ Anthropic integration

**You can test this now:** 
- Query: "best toy under $30?"
- Should return: Ms. Rachel + Glitter Dumpling with product cards

---

## 🎯 What We're Adding: Real-Time API Product Search

Right now, the system only returns products from the static PRODUCTS array (10 items). We're adding:

1. **Walmart Product Search API** - Search their full catalog
2. **Impact Affiliate Link Generation** - Create goto.walmart.com links
3. **Crawlbase Amazon Scraping** - Get Amazon products (Phase 2)
4. **Smart Product Resolver** - CVR-based routing logic

---

## 📦 Step 1: Add Dependencies

Update `pyproject.toml` to include new dependencies:

```toml
[project]
name = "repl-nix-workspace"
version = "0.1.0"
description = "Add your description here"
requires-python = ">=3.11"
dependencies = [
    "anthropic>=0.85.0",
    "flask>=3.1.3",
    "gunicorn>=25.1.0",
    "requests>=2.31.0",
    "beautifulsoup4>=4.12.3",
    "lxml>=5.1.0",
]
```

**Changes:** Added `requests`, `beautifulsoup4`, `lxml`

**In Replit:** The packages should auto-install. If not, click "Install packages" or run:
```bash
uv pip install requests beautifulsoup4 lxml
```

---

## 📝 Step 2: Add product_api.py

Create a **new file** in your repo root: `product_api.py`

Copy the entire contents from the `product_api.py` file I provided earlier.

**This file contains:**
- `WalmartAPI` class
- `CrawlbaseAPI` class
- `ImpactAPI` class
- `ProductResolver` class
- Helper functions

**Location:** Same directory as `app.py`

---

## 🔧 Step 3: Update app.py

Your current `app.py` works with the Hot Score catalog. Now we need to add API fallback.

**Add this import at the top:**
```python
from product_api import ProductResolver, detect_category
```

**Add this after the PRODUCTS array (around line 20):**
```python
# Initialize product resolver
product_resolver = ProductResolver(PRODUCTS)
```

**Update the SYSTEM_PROMPT** to include the SEARCH option:

Replace the current SYSTEM_PROMPT with this updated version:

```python
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

PRODUCT RECOMMENDATION FORMAT:
When recommending products, end your response with a line containing ONLY product IDs in this exact format:
PRODUCTS: 0,1,2

If you don't have exact matches in the catalog, end with:
SEARCH: category_keyword

Examples:
User: "best toy under $30?"
Response: "oooh I have the PERFECT picks for you! The Ms. Rachel set is only $7 at Walmart right now (56% off 😱), or the Glitter Dumpling Squishy for $13.49 — my kids are OBSESSED with it. Both are total winners!
PRODUCTS: 2,1"

User: "show me cheap home decor"
Response: "Let me find you some amazing home finds at great prices!
SEARCH: home decor budget"

Always include PRODUCTS: line if you mention specific items by name, or SEARCH: if you need to find products."""
```

**Update the /api/chat endpoint** to handle SEARCH:

Replace the current chat() function with this:

```python
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get('message') or '').strip()
    if not user_message:
        return jsonify({'error': 'message is required'}), 400

    try:
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        message = client.messages.create(
            model='claude-opus-4-1-20250805',
            max_tokens=256,
            system=SYSTEM_PROMPT,
            messages=[{'role': 'user', 'content': user_message}],
        )
        reply = message.content[0].text
        
        # Parse product recommendations from response
        products = []
        text_reply = reply
        
        if 'PRODUCTS:' in reply:
            # Claude referenced specific Hot Score products
            parts = reply.split('PRODUCTS:')
            text_reply = parts[0].strip()
            product_ids_str = parts[1].strip()
            
            # Extract product IDs (comma-separated integers)
            try:
                product_ids = [int(pid.strip()) for pid in product_ids_str.split(',')]
                products = [PRODUCTS[pid] for pid in product_ids if 0 <= pid < len(PRODUCTS)]
            except (ValueError, IndexError):
                pass  # If parsing fails, just return text without products
        
        elif 'SEARCH:' in reply:
            # Claude needs to search via APIs
            parts = reply.split('SEARCH:')
            text_reply = parts[0].strip()
            search_query = parts[1].strip()
            
            # Detect category from query
            category = detect_category(search_query)
            
            # Use product resolver to find products
            try:
                resolved_products = product_resolver.resolve(search_query, category, max_results=3)
                products = resolved_products
            except Exception as e:
                print(f"Product resolution error: {e}")
                # Fallback to empty products array
                products = []
        
        return jsonify({
            'reply': text_reply,
            'products': products
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

## 🔐 Step 4: Verify Replit Secrets

Make sure these 6 secrets are set in Replit (Tools → Secrets):

```
✓ ANTHROPIC_API_KEY
✓ WALMART_API_PUBLIC_KEY
✓ WALMART_API_PRIVATE_KEY
✓ CRAWLBASE_JS_TOKEN
✓ IMPACT_ACCOUNT_SID
✓ IMPACT_AUTH_TOKEN
```

---

## 🧪 Step 5: Test the System

### Test 1: Hot Score Products (Should Already Work)
**Query:** "best toy under $30?"  
**Expected:** Ms. Rachel + Glitter Dumpling cards appear  
**How it works:** Claude returns `PRODUCTS: 2,1` → Backend returns from PRODUCTS array

---

### Test 2: Walmart API Search (New!)
**Query:** "show me cheap kitchen gadgets"  
**Expected:** 
1. Claude returns `SEARCH: kitchen gadgets cheap`
2. ProductResolver calls Walmart API
3. Returns 3 Walmart products
4. Impact affiliate links generated
5. Product cards appear in chat

**Check console for:**
```
🔍 Walmart API called with query: kitchen gadgets cheap
```

---

### Test 3: Impact Links
**Click:** "Shop Now" button on a Walmart product  
**Expected URL format:**
```
https://goto.walmart.com/c/3590891/1398372/16662?veh=aff&u=https%3A%2F%2Fwww.walmart.com%2Fip%2F...&subId1=chat-recommendation&subId2=SKU
```

---

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'product_api'"
**Fix:** Make sure `product_api.py` is in the same directory as `app.py`

### Error: "Walmart API returns 401 Unauthorized"
**Fix:** 
1. Check WALMART_API_PUBLIC_KEY and WALMART_API_PRIVATE_KEY in Secrets
2. Verify the keys are correct (copy-paste from Walmart developer dashboard)

### Error: "Product resolution error: ..."
**Fix:** Check the Replit console for specific error message. Common causes:
- API rate limiting
- Invalid API credentials
- Network timeout

### Walmart API returns empty results
**Debug:** Add print statements to see the API response:

In `product_api.py`, inside `WalmartAPI.search()`:
```python
response = requests.get(endpoint, params=params, headers=headers, timeout=10)
print(f"Walmart API Status: {response.status_code}")
print(f"Walmart API Response: {response.text[:500]}")
```

---

## 📊 System Flow Diagram

```
User: "show me cheap kitchen gadgets"
       ↓
Claude receives query + SYSTEM_PROMPT
       ↓
Claude: "Let me find some great kitchen finds!
         SEARCH: kitchen gadgets cheap"
       ↓
Backend parses "SEARCH:" line
       ↓
detect_category("kitchen gadgets cheap") → "home"
       ↓
ProductResolver.resolve(query, category="home", max_results=3)
       ↓
  Step 1: Search Hot Score catalog → 0 matches
  Step 2: CVR rules say: home → Wayfair first, fallback Walmart
  Step 3: Call Walmart API (fallback logic)
  Step 4: Walmart returns 3 products
  Step 5: Generate Impact links for each
       ↓
Backend returns: {'reply': text, 'products': [3 Walmart products]}
       ↓
Frontend renders 3 product cards
```

---

## ✅ Verification Checklist

After making changes:

- [ ] Dependencies installed (`requests`, `beautifulsoup4`, `lxml`)
- [ ] `product_api.py` file added to repo
- [ ] `app.py` updated with imports and SEARCH handling
- [ ] All 6 API secrets verified in Replit
- [ ] Hot Score queries still work ("best toy under $30")
- [ ] Walmart API queries work ("cheap kitchen gadgets")
- [ ] Impact links have correct format (goto.walmart.com)
- [ ] Product cards render correctly
- [ ] No console errors

---

## 🚀 Commit to GitHub

Once everything works:

```bash
git add product_api.py
git add app.py
git add pyproject.toml
git commit -m "Add Walmart API integration and product resolver"
git push origin main
```

---

## 🔜 Next Steps (After This Works)

1. **Implement Crawlbase parsing** - Full Amazon product search
2. **Add product caching** - SQLite database for search results
3. **URLGenius integration** - Pull existing 1,347 links
4. **Hot Score refresh** - Background job every 2 days
5. **Analytics tracking** - Track product click events

---

## 💬 What to Report Back

1. Did Walmart API search work?
2. Are Impact links generating correctly?
3. What's the actual Campaign ID from your Impact dashboard?
4. Any errors in the Replit console?

---

*Ready to integrate! Add `product_api.py`, update `app.py`, and test.*
