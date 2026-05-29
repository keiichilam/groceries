"""
T&T Supermarket live scraper — Metro Vancouver F&V products.

tntsupermarket.com uses Magento GraphQL. The GetCategories query
includes a `products.items[]` array with pricing.

Output (stdout): {"chain":"tnt","stores":[...],"inventory":[...]}
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from common import delay, output
from camoufox.async_api import AsyncCamoufox

CHAIN = "tnt"
BASE_URL = "https://www.tntsupermarket.com"
CATEGORY_URL = f"{BASE_URL}/eng/product-categories/tt-fruits-vegetables.html"

KNOWN_STORES = [
    {"id": "tnt-metrotown", "name": "T&T Supermarket Metrotown", "lat": 49.2276, "lng": -122.9998},
    {"id": "tnt-richmond",  "name": "T&T Supermarket Richmond",  "lat": 49.1666, "lng": -123.1336},
    {"id": "tnt-downtown",  "name": "T&T Supermarket Downtown",  "lat": 49.2827, "lng": -123.1207},
]


def _parse_graphql_products(payload: dict) -> list[dict]:
    """Extract items from a GetCategories GraphQL response."""
    items: list[dict] = []
    prods = payload.get("data", {}).get("products", {})
    raw_items = prods.get("items") or []
    for p in raw_items:
        try:
            name = p.get("name", "").strip()
            if not name:
                continue
            price = (
                p.get("price_range", {})
                 .get("minimum_price", {})
                 .get("final_price", {})
                 .get("value", 0)
            )
            price = float(price)
            if price <= 0:
                continue
            in_stock = p.get("stock_status", "IN_STOCK") == "IN_STOCK"
            items.append({
                "itemName": name,
                "category": "Produce",
                "price": round(price, 2),
                "inStock": in_stock,
            })
        except Exception:
            continue
    return items


async def scrape_category(page) -> list[dict]:
    captured: list[dict] = []

    async def on_response(response):
        if "graphql" not in response.url or response.status != 200:
            return
        try:
            data = await response.json()
            prods = data.get("data", {}).get("products", {})
            if prods and prods.get("items"):
                captured.append(data)
        except Exception:
            pass

    page.on("response", on_response)
    try:
        await page.goto(CATEGORY_URL, wait_until="domcontentloaded", timeout=30000)
        # Scroll repeatedly to trigger pagination loads
        for _ in range(6):
            await page.keyboard.press("End")
            await asyncio.sleep(2)
    except Exception as e:
        print(f"[tnt] page error: {e}", file=sys.stderr)
    finally:
        page.remove_listener("response", on_response)

    items: list[dict] = []
    seen_names: set[str] = set()
    for payload in captured:
        for item in _parse_graphql_products(payload):
            if item["itemName"] not in seen_names:
                seen_names.add(item["itemName"])
                items.append(item)
    return items


async def main():
    inventory: list[dict] = []

    async with AsyncCamoufox(headless=True) as browser:
        page = await browser.new_page()
        print("[tnt] scraping GraphQL category page ...", file=sys.stderr)
        items = await scrape_category(page)
        print(f"[tnt]   → {len(items)} F&V items", file=sys.stderr)
        # T&T doesn't expose per-branch pricing online; apply to all stores
        for store in KNOWN_STORES:
            for item in items:
                inventory.append({**item, "storeId": store["id"]})

    output({"chain": CHAIN, "stores": KNOWN_STORES, "inventory": inventory})


if __name__ == "__main__":
    asyncio.run(main())
