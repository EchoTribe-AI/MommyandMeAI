# This shows ONLY the changes needed to your current app.py
# Copy the sections below and integrate them into your existing app.py

# ═══════════════════════════════════════════════════
# SECTION 1: ADD TO TOP OF FILE (after other imports)
# ═══════════════════════════════════════════════════

from product_api import ProductResolver, detect_category


# ═══════════════════════════════════════════════════
# SECTION 2: ADD AFTER PRODUCTS ARRAY (around line 20)
# ═══════════════════════════════════════════════════

# Initialize product resolver
product_resolver = ProductResolver(PRODUCTS)


# ═══════════════════════════════════════════════════
# SECTION 3: UPDATE SYSTEM_PROMPT
# Replace the existing SYSTEM_PROMPT with this version
# ═══════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════
# SECTION 4: UPDATE THE /api/chat ENDPOINT
# Replace the entire chat() function with this version
# ═══════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════
# That's it! The rest of app.py stays the same.
# ═══════════════════════════════════════════════════
