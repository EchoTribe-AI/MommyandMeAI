import requests
import json
import os

api_key = os.environ.get("URLGENIUS_API_KEY")

# Hit the base endpoint with no pagination params first
url = "https://api.urlgeni.us/api/v2/links"

response = requests.get(url, headers={"api-key": api_key})

print("=== STATUS CODE ===")
print(response.status_code)

print("\n=== RESPONSE HEADERS (pagination-related) ===")
for k, v in response.headers.items():
    if any(x in k.lower() for x in ["link", "cursor", "page", "next", "total", "count"]):
        print(f"  {k}: {v}")

print("\n=== FULL RESPONSE (first 3000 chars) ===")
raw = response.text[:3000]
print(raw)

print("\n=== TOP-LEVEL KEYS ===")
try:
    data = response.json()
    print(list(data.keys()) if isinstance(data, dict) else f"Array of {len(data)} items")

    # Look for pagination fields
    if isinstance(data, dict):
        for key in data:
            val = data[key]
            if not isinstance(val, list):
                print(f"  {key}: {val}")
            else:
                print(f"  {key}: [array of {len(val)} items]")
except Exception as e:
    print(f"JSON parse error: {e}")

# Also try hitting with page=2 to see if offset style works at all
print("\n=== TRYING ?page=2 ===")
r2 = requests.get("https://api.urlgeni.us/api/v2/links", headers={"api-key": api_key}, params={"page": 2})
print(f"Status: {r2.status_code}")
try:
    d2 = r2.json()
    print(f"Top keys: {list(d2.keys()) if isinstance(d2, dict) else 'array'}")
    if isinstance(d2, dict):
        for key in d2:
            if not isinstance(d2[key], list):
                print(f"  {key}: {d2[key]}")
except:
    print(r2.text[:500])
