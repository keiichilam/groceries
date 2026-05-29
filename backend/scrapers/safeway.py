"""
Safeway Canada scraper — Metro Vancouver F&V products.

Safeway shares the same Sobeys/Algolia stack as FreshCo (app ACSYSHF8AU,
index dxp_product_en). Set localStorage storeId, navigate to the produce
category page, intercept Algolia product responses.

Output (stdout): {"chain":"safeway","stores":[...],"inventory":[...]}
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from common import delay, make_item_id, is_produce, output
from camoufox.async_api import AsyncCamoufox

CHAIN = "safeway"
BASE_URL = "https://www.safeway.ca"
CATEGORY_URL = f"{BASE_URL}/products/category/Fresh%20Fruits%20%26%20Vegetables"

# Metro Vancouver Safeway stores (objectID from Algolia dxp_stores index)
KNOWN_STORES = [
    {"id": "safeway-north-van-westview",  "name": "Safeway Westview Mall",   "lat": 49.3331,   "lng": -123.0909, "storeId": "4905"},
    {"id": "safeway-north-van-lynn",      "name": "Safeway Lynn Valley",     "lat": 49.3342,   "lng": -123.0419, "storeId": "4950"},
    {"id": "safeway-vancouver-robson",    "name": "Safeway Robson",          "lat": 49.290778, "lng": -123.135023, "storeId": "4908"},
    {"id": "safeway-vancouver-davie",     "name": "Safeway Davie Street",    "lat": 49.285748, "lng": -123.138921, "storeId": "4998"},
]


def _parse_algolia_products(payload: dict, store_id: str) -> list[dict]:
    items: list[dict] = []
    results = payload.get("results", [payload])
    for r in results:
        for hit in r.get("hits", []):
            try:
                name = hit.get("name", "").strip()
                if not name:
                    continue
                cats = hit.get("hierarchicalCategories", {})
                lvl0 = cats.get("lvl0", [])
                if isinstance(lvl0, str):
                    lvl0 = [lvl0]
                if not any("fruit" in c.lower() or "vegetable" in c.lower() for c in lvl0):
                    if not is_produce(name, ""):
                        continue
                price = float(hit.get("price", 0) or 0)
                if price <= 0:
                    continue
                in_stock = hit.get("inStock", True)
                category = lvl0[0] if lvl0 else "Produce"
                items.append({
                    "storeId": store_id,
                    "itemName": name,
                    "category": category,
                    "price": round(price, 2),
                    "inStock": bool(in_stock),
                })
            except Exception:
                continue
    return items


async def scrape_store(page, store: dict) -> list[dict]:
    captured: list[dict] = []

    async def on_response(response):
        if "algolia" not in response.url or response.status != 200:
            return
        try:
            data = await response.json()
            results = data.get("results", [data])
            if any(r.get("hits") and "price" in r["hits"][0] for r in results if r.get("hits")):
                captured.append(data)
        except Exception:
            pass

    page.on("response", on_response)
    try:
        await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        sid = store["storeId"]
        await page.evaluate(f"localStorage.setItem('storeId', '{sid}')")
        await page.goto(CATEGORY_URL, wait_until="domcontentloaded", timeout=30000)
        for _ in range(5):
            await page.keyboard.press("End")
            await asyncio.sleep(2)
    except Exception as e:
        print(f"[safeway] error for {store['id']}: {e}", file=sys.stderr)
    finally:
        page.remove_listener("response", on_response)

    items: list[dict] = []
    seen: set[str] = set()
    for payload in captured:
        for item in _parse_algolia_products(payload, store["id"]):
            key = item["itemName"]
            if key not in seen:
                seen.add(key)
                items.append(item)
    return items


async def main():
    inventory: list[dict] = []

    async with AsyncCamoufox(headless=True) as browser:
        page = await browser.new_page()
        for store in KNOWN_STORES:
            print(f"[safeway] scraping {store['name']} ...", file=sys.stderr)
            items = await scrape_store(page, store)
            inventory.extend(items)
            print(f"[safeway]   → {len(items)} F&V items", file=sys.stderr)
            await delay(3000)

    output({"chain": CHAIN, "stores": KNOWN_STORES, "inventory": inventory})


if __name__ == "__main__":
    asyncio.run(main())
