"""
Save-On-Foods scraper — Metro Vancouver F&V products.

Products are server-side rendered into window.__PRELOADED_STATE__ under
departments.productCardDictionary. Navigate to the store-specific produce
category URL and extract from the state object.

Output (stdout): {"chain":"saveon","stores":[...],"inventory":[...]}
"""
import asyncio
import json
import re
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from common import delay, is_produce, output
from camoufox.async_api import AsyncCamoufox

CHAIN = "saveon"
BASE_URL = "https://www.saveonfoods.com"
# Category ID 30681 = Fruits & Vegetables
CATEGORY_PATH = "/categories/fruits-vegetables-id-30681"

# Representative Metro Vancouver Save-On-Foods stores (rsid from storefrontgateway API)
KNOWN_STORES = [
    {"id": "saveon-burnaby-cameron",     "name": "Save-On-Foods Cameron (Burnaby)",       "lat": 49.2524643, "lng": -122.8941771, "rsid": "2221"},
    {"id": "saveon-burnaby-highgate",    "name": "Save-On-Foods HighGate Village (Burnaby)", "lat": 49.21867, "lng": -122.95639,   "rsid": "907"},
    {"id": "saveon-vancouver-grandview", "name": "Save-On-Foods Grandview (Vancouver)",   "lat": 49.2585,   "lng": -123.03192,   "rsid": "961"},
    {"id": "saveon-vancouver-main",      "name": "Save-On-Foods Main Street (Vancouver)", "lat": 49.25866,  "lng": -123.10145,   "rsid": "2219"},
    {"id": "saveon-richmond-terra-nova", "name": "Save-On-Foods Terra Nova (Richmond)",   "lat": 49.17006,  "lng": -123.18269,   "rsid": "971"},
]


def _extract_products(html: str, store_id: str) -> list[dict]:
    """Pull products from window.__PRELOADED_STATE__.departments.productCardDictionary."""
    items: list[dict] = []
    m = re.search(r"window\.__PRELOADED_STATE__\s*=\s*(\{.+)", html)
    if not m:
        return items

    raw = m.group(1)
    try:
        state, _ = json.JSONDecoder().raw_decode(raw)
    except Exception as e:
        print(f"[saveon] JSON parse error: {e}", file=sys.stderr)
        return items

    product_dict = (
        state.get("departments", {})
             .get("productCardDictionary", {})
    )
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
            import re as _re
            price_raw = str(product.get("price", "0") or "0")
            price_match = _re.search(r"[\d]+\.?[\d]*", price_raw)
            price = float(price_match.group()) if price_match else 0.0
            if price <= 0:
                continue
            available = product.get("available", True)
            category = cats[0].get("category", "Produce") if cats else "Produce"
            items.append({
                "storeId": store_id,
                "itemName": name,
                "category": category,
                "price": round(price, 2),
                "inStock": bool(available),
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
        print(f"[saveon] error for {store['id']}: {e}", file=sys.stderr)
        return []

    html = await page.content()
    has_state = "window.__PRELOADED_STATE__" in html
    print(f"[saveon]   html={len(html)}B has_state={has_state}", file=sys.stderr)
    items = _extract_products(html, store["id"])
    return items


async def main():
    inventory: list[dict] = []

    async with AsyncCamoufox(headless=True) as browser:
        page = await browser.new_page()
        for store in KNOWN_STORES:
            print(f"[saveon] scraping {store['name']} ...", file=sys.stderr)
            items = await scrape_store(page, store)
            inventory.extend(items)
            print(f"[saveon]   → {len(items)} F&V items", file=sys.stderr)
            await delay(2000)

    output({"chain": CHAIN, "stores": KNOWN_STORES, "inventory": inventory})


if __name__ == "__main__":
    asyncio.run(main())
