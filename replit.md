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
- Python 3.11
- Flask

## Running
```
python app.py
```
Server runs on port 5000.
