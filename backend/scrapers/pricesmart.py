"""
PriceSmart Foods scraper — Metro Vancouver F&V products.

PriceSmart is owned by Overwaitea Food Group (same as Save-On-Foods) and
shares the identical backend stack: storefrontgateway.pricesmartfoods.com,
window.__PRELOADED_STATE__, category ID 30681 for Fruits & Vegetables.

Output (stdout): {"chain":"pricesmart","stores":[...],"inventory":[...]}
"""
import asyncio
import json
import re
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from common import delay, is_produce, output
from camoufox.async_api import AsyncCamoufox

CHAIN = "pricesmart"
BASE_URL = "https://www.pricesmartfoods.com"
CATEGORY_PATH = "/categories/fruits-vegetables-id-30681"

KNOWN_STORES = [
    {"id": "pricesmart-richmond-ackroyd",    "name": "PriceSmart Foods Richmond (Ackroyd)",       "lat": 49.17184,    "lng": -123.13319,  "rsid": "2274"},
    {"id": "pricesmart-burnaby-station-sq",  "name": "PriceSmart Foods Station Square (Burnaby)", "lat": 49.22892,    "lng": -123.00122,  "rsid": "2281"},
    {"id": "pricesmart-burnaby-lougheed",    "name": "PriceSmart Foods Lougheed (Burnaby)",       "lat": 49.25002,    "lng": -122.89399,  "rsid": "2280"},
    {"id": "pricesmart-vancouver-broadway",  "name": "PriceSmart Foods Broadway (Vancouver)",     "lat": 49.2626679,  "lng": -123.0997639,"rsid": "2275"},
    {"id": "pricesmart-burnaby-kings",       "name": "PriceSmart Foods Kings Crossing (Burnaby)", "lat": 49.2192198,  "lng": -122.9498123,"rsid": "2276"},
]


def _extract_products(html: str, store_id: str) -> list[dict]:
    items: list[dict] = []
    m = re.search(r"window\.__PRELOADED_STATE__\s*=\s*(\{.+)", html)
    if not m:
        return items
    try:
        state, _ = json.JSONDecoder().raw_decode(m.group(1))
    except Exception as e:
        print(f"[pricesmart] JSON parse error: {e}", file=sys.stderr)
        return items

    product_dict = state.get("departments", {}).get("productCardDictionary", {})
    if not isinstance(product_dict, dict):
        return items

    for product in product_dict.values():
        if not isinstance(product, dict):
            continue
        try:
            name = product.get("name", "").strip()
            if not name:
                continue
            cats = product.get("categories", [])
            cat_names = " ".join(c.get("category", "") for c in cats if isinstance(c, dict))
            if not is_produce(name, cat_names):
                continue
            price_raw = str(product.get("price", "0") or "0")
            price_match = re.search(r"[\d]+\.?[\d]*", price_raw)
            price = float(price_match.group()) if price_match else 0.0
            if price <= 0:
                continue
            category = cats[0].get("category", "Produce") if cats else "Produce"
            items.append({
                "storeId": store_id,
                "itemName": name,
                "category": category,
                "price": round(price, 2),
                "inStock": bool(product.get("available", True)),
            })
        except Exception:
            continue
    return items


async def scrape_store(page, store: dict) -> list[dict]:
    url = f"{BASE_URL}/sm/planning/rsid/{store['rsid']}{CATEGORY_PATH}"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(7)
    except Exception as e:
        print(f"[pricesmart] error for {store['id']}: {e}", file=sys.stderr)
        return []
    return _extract_products(await page.content(), store["id"])


async def main():
    inventory: list[dict] = []

    async with AsyncCamoufox(headless=True) as browser:
        page = await browser.new_page()
        for store in KNOWN_STORES:
            print(f"[pricesmart] scraping {store['name']} ...", file=sys.stderr)
            items = await scrape_store(page, store)
            inventory.extend(items)
            print(f"[pricesmart]   → {len(items)} F&V items", file=sys.stderr)
            await delay(2000)

    output({"chain": CHAIN, "stores": KNOWN_STORES, "inventory": inventory})


if __name__ == "__main__":
    asyncio.run(main())
