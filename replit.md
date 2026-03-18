# Mommy & Me Collective — AI Agent App

## Overview
A Flask web application with a prototype app demo as the home page, plus three linked strategy/architecture documents navigable via a sticky tab bar.

## Structure
- `app.py` — Flask server on port 5000
- `index.html` — App prototype (home page: Visitor View + Team Dashboard)
- `steph-ai-plan.html` — AI Agent Strategy Plan
- `steph-architecture.html` — AI Agent Architecture Map
- `steph-connection-map.html` — Storefront Audit & Data Connection Map
- `zipFile.zip` — Original uploaded zip with initial HTML files

## Routes
- `/` — App prototype (Visitor View + Team Dashboard)
- `/plan` — AI Agent Strategy Plan
- `/architecture` — Architecture Map
- `/connections` — Storefront & Data Connection Map

## Navigation
- Home page (prototype) has no tab bar — it's standalone
- The 3 doc pages (/plan, /architecture, /connections) each have a sticky top nav with:
  - "← Home" button (returns to prototype)
  - 3 tabs: Build Plan / Architecture / Connections (active tab highlighted with coral underline)

## Tech Stack
- Python 3.11 + Flask
- Claude AI (Anthropic Opus) for chat responses
- Product Resolver with CVR routing logic
- Walmart, Crawlbase, and Impact API integrations
- Responsive HTML/CSS/JavaScript frontend

## Features

### Chat with Product Recommendations (Phase 1: Complete ✅)
- **Smart Chat Interface** — Users ask via suggestion buttons or free text
- **Claude AI Integration** — Claude Opus recommends products with `PRODUCTS:` or `SEARCH:` directives
- **Dual Product Source:**
  - **Hot Score Catalog** (10 curated products) — Static, always available
  - **API Search** (Real-time Walmart products) — Via SEARCH: fallback when Hot Score doesn't match
- **Product Cards** — Mobile-responsive cards with emoji, price, savings %, retailer, affiliate "Shop Now" link
- **Smart Routing** — CVR-based retailer selection:
  - Toys/Baby/Kids → Walmart (16.7% CVR)
  - Beauty → Ulta ($270+ revenue per product)
  - Home → Wayfair (highest AOV)
  - Household/Food → Amazon ($80K+ YTD)

### Product Catalog
**Hot Score Catalog:** 10 curated, high-performing products  
**API Integration:** Walmart product search + real-time availability (when API keys configured)

### How It Works
1. User clicks suggestion chip or types question
2. `sendChat()` sends to `/api/chat` endpoint
3. Claude Opus decides: `PRODUCTS: 0,1,2` (use Hot Score) or `SEARCH: query` (search APIs)
4. **If PRODUCTS:** Backend returns matching products from PRODUCTS array
5. **If SEARCH:** ProductResolver:
   - Detects category
   - Checks CVR routing rules
   - Calls appropriate API (Walmart first for toys/baby)
   - Generates Impact affiliate links
   - Returns real-time products
6. Frontend renders Steph's reply + product cards with affiliate links

## Running
```
python app.py
```
Server runs on port 5000.

## Configuration

### Required (Already Set ✅)
- **ANTHROPIC_API_KEY** — Enables Claude chat (configured)

### Optional (For Real-Time Walmart API Search)
To enable SEARCH: fallback, configure these in Replit Secrets:
- **WALMART_API_PUBLIC_KEY** — From Walmart Developer Portal
- **WALMART_API_PRIVATE_KEY** — From Walmart Developer Portal
- **IMPACT_ACCOUNT_SID** — From Impact.com dashboard
- **IMPACT_AUTH_TOKEN** — From Impact.com dashboard
- **CRAWLBASE_JS_TOKEN** — From Crawlbase dashboard (for Amazon scraping)

**Current Status:** Hot Score products work fully. API search will activate once keys are added.

## Files

- `app.py` — Flask server with chat endpoint + product resolver initialization
- `product_api.py` — ProductResolver class + Walmart/Crawlbase/Impact API integrations
- `index.html` — Frontend with product cards UI
- `pyproject.toml` — Dependencies: anthropic, flask, gunicorn, requests, beautifulsoup4, lxml
