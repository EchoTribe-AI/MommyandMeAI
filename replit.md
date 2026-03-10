# Mommy & Me Collective — AI Agent Strategy App

## Overview
A Flask web application serving three HTML strategy/architecture documents for the Mommy & Me Collective AI Agent project, with tab navigation between pages.

## Structure
- `app.py` — Flask server serving static HTML pages on port 5000
- `steph-ai-plan.html` — AI Agent Strategy Plan document (home page)
- `steph-architecture.html` — AI Agent Architecture Map document
- `steph-connection-map.html` — Storefront Audit & Data Connection Map
- `zipFile.zip` — Original uploaded zip containing initial HTML files

## Routes
- `/` or `/plan` — AI Agent Strategy Plan (home)
- `/architecture` — Architecture Map
- `/connections` — Storefront & Data Connection Map

## Navigation
All pages have a sticky tab bar at the top with 3 tabs: Build Plan, Architecture, Connections. Active tab is highlighted with a coral underline.

## Tech Stack
- Python 3.11
- Flask

## Running
```
python app.py
```
Server runs on port 5000.
