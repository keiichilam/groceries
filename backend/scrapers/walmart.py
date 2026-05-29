"""
Walmart Canada scraper — Metro Vancouver F&V products.

Uses network interception to capture Walmart's internal product API responses
rather than DOM parsing, which is more resilient to layout changes.

Output (stdout): {"chain":"walmart","stores":[...],"inventory":[...]}
"""
import asyncio
import json
import sys
import os
import re
sys.path.insert(0, os.path.dirname(__file__))
from common import delay, make_item_id, is_produce, output, error_exit, dismiss_overlays, METRO_VAN_POSTAL
from camoufox.async_api import AsyncCamoufox

CHAIN = "walmart"
BASE_URL = "https://www.walmart.ca"
STORE_API_PATTERN = re.compile(r"nearby-stores|store-finder|nearby_stores", re.I)
PRODUCT_API_PATTERN = re.compile(r"search/products|browse/products|search-result|graphql", re.I)
CATEGORY_URLS = [
    f"{BASE_URL}/en/grocery/fruits-vegetables",
    f"{BASE_URL}/browse/fruits-vegetables",
    f"{BASE_URL}/en/food/produce",
]

# Known Metro Vancouver Walmart locations as fallback if API discovery fails
KNOWN_STORES = [
    {"id": "walmart-burnaby-metrotown", "name": "Walmart Supercentre Burnaby Metrotown",
     "lat": 49.2258, "lng": -122.9989, "postalCode": "V5H 1L3"},
    {"id": "walmart-richmond-no3rd",    "name": "Walmart Supercentre Richmond",
     "lat": 49.1654, "lng": -123.0726, "postalCode": "V6X 2C5"},
    {"id": "walmart-vancouver-grandview", "name": "Walmart Supercentre Vancouver",
     "lat": 49.2603, "lng": -123.0691, "postalCode": "V5N 0A3"},
]


async def find_stores(page) -> list[dict]:
    """Navigate to store finder and intercept the stores API response."""
    captured: list[dict] = []

    async def on_response(response):
        if STORE_API_PATTERN.search(response.url) and response.status == 200:
            try:
                ct = response.headers.get("content-type", "")
                if "json" in ct:
                    data = await response.json()
                    captured.append(data)
            except Exception:
                pass

    page.on("response", on_response)
    try:
        await page.goto(f"{BASE_URL}/en/stores-near-me", wait_until="networkidle", timeout=30000)
        await dismiss_overlays(page)
        # Type postal code into store search if available
        search_input = page.locator("input[placeholder*='postal' i], input[placeholder*='city' i], input[type='search']").first
        if await search_input.is_visible(timeout=3000):
            await search_input.fill(METRO_VAN_POSTAL)
            await search_input.press("Enter")
            await page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    finally:
        page.remove_listener("response", on_response)

    stores: list[dict] = []
    for payload in captured:
        stores.extend(_parse_store_payload(payload))

    if not stores:
        print("[walmart] store API not captured, using known locations", file=sys.stderr)
        return KNOWN_STORES

    return stores


def _parse_store_payload(payload) -> list[dict]:
    stores: list[dict] = []
    candidates = []
    if isinstance(payload, list):
        candidates = payload
    elif isinstance(payload, dict):
        for key in ("stores", "items", "results", "data"):
            if key in payload and isinstance(payload[key], list):
                candidates = payload[key]
                break

    for s in candidates:
        try:
            lat = float(s.get("latitude") or s.get("lat") or s.get("geoPoint", {}).get("lat", 0))
            lng = float(s.get("longitude") or s.get("lng") or s.get("lon") or s.get("geoPoint", {}).get("lon", 0))
            name = s.get("displayName") or s.get("name") or s.get("storeName") or ""
            store_id = s.get("storeId") or s.get("id") or ""
            if lat and lng and name and "Vancouver" in (s.get("city") or "") or "Burnaby" in (s.get("city") or "") or "Richmond" in (s.get("city") or ""):
                slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
                stores.append({
                    "id": f"walmart-{slug[:40]}",
                    "name": name,
                    "lat": lat,
                    "lng": lng,
                    "storeId": str(store_id),
                })
        except Exception:
            continue
    return stores


async def scrape_products(page, store: dict) -> list[dict]:
    """Intercept Walmart's product API while browsing the F&V category."""
    captured: list[dict] = []

    async def on_response(response):
        if PRODUCT_API_PATTERN.search(response.url) and response.status == 200:
            try:
                ct = response.headers.get("content-type", "")
                if "json" in ct:
                    data = await response.json()
                    captured.append({"url": response.url, "data": data})
            except Exception:
                pass

    page.on("response", on_response)
    try:
        store_id = store.get("storeId", "")
        qs = f"?storeId={store_id}" if store_id else ""
        for base_url in CATEGORY_URLS:
            try:
                await page.goto(base_url + qs, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)  # let XHR settle
                break
            except Exception as e:
                print(f"[walmart] trying next URL (error: {e})", file=sys.stderr)
        await dismiss_overlays(page)
        await delay()
        # Scroll to trigger lazy loading
        for _ in range(3):
            await page.keyboard.press("End")
            await asyncio.sleep(1.5)
    except Exception as e:
        print(f"[walmart] product page error for {store['id']}: {e}", file=sys.stderr)
    finally:
        page.remove_listener("response", on_response)

    items: list[dict] = []
    for entry in captured:
        items.extend(_parse_product_payload(entry["data"], store["id"]))

    if not items:
        # Fallback: parse DOM product cards
        items.extend(await _parse_dom_products(page, store["id"]))

    return items


def _parse_product_payload(payload, store_id: str) -> list[dict]:
    items: list[dict] = []
    candidates: list[dict] = []

    def collect(obj):
        if isinstance(obj, list):
            for item in obj:
                collect(item)
        elif isinstance(obj, dict):
            if "name" in obj and ("price" in obj or "salePrice" in obj or "currentPrice" in obj):
                candidates.append(obj)
            else:
                for v in obj.values():
                    collect(v)

    collect(payload)

    for p in candidates:
        try:
            name = p.get("name") or p.get("displayName") or p.get("title") or ""
            category = p.get("category") or p.get("categoryName") or "Produce"
            if not name or not is_produce(name, category):
                continue
            price_raw = (p.get("salePrice") or p.get("currentPrice") or
                         p.get("price") or p.get("priceInfo", {}).get("currentPrice", 0))
            try:
                price = float(str(price_raw).replace("$", "").replace(",", "").strip())
            except Exception:
                continue
            if price <= 0:
                continue
            in_stock = p.get("availabilityStatus") != "OUT_OF_STOCK" and p.get("inStock", True)
            items.append({
                "storeId": store_id,
                "itemName": name.strip(),
                "category": category,
                "price": round(price, 2),
                "inStock": bool(in_stock),
            })
        except Exception:
            continue
    return items


async def _parse_dom_products(page, store_id: str) -> list[dict]:
    """DOM fallback: grab product cards visible on the page."""
    items: list[dict] = []
    try:
        cards = await page.locator("[data-automation-id='product-title'], [itemprop='name']").all()
        for card in cards[:60]:
            try:
                name = (await card.inner_text()).strip()
                if not is_produce(name, ""):
                    continue
                # Try to find price sibling
                parent = card.locator("xpath=ancestor::*[contains(@class,'product')]").first
                price_el = parent.locator("[data-automation-id='product-price'], [itemprop='price']").first
                price_text = (await price_el.inner_text(timeout=1000)).strip()
                price = float(re.sub(r"[^0-9.]", "", price_text) or "0")
                if price <= 0:
                    continue
                items.append({
                    "storeId": store_id,
                    "itemName": name,
                    "category": "Produce",
                    "price": round(price, 2),
                    "inStock": True,
                })
            except Exception:
                continue
    except Exception:
        pass
    return items


async def main():
    inventory: list[dict] = []
    stores: list[dict] = []

    async with AsyncCamoufox(headless=True) as browser:
        page = await browser.new_page()
        stores = await find_stores(page)
        await delay(2000)

        for store in stores:
            print(f"[walmart] scraping {store['name']} ...", file=sys.stderr)
            products = await scrape_products(page, store)
            inventory.extend(products)
            print(f"[walmart]   → {len(products)} F&V items", file=sys.stderr)
            await delay(2000)

    output({"chain": CHAIN, "stores": stores, "inventory": inventory})


if __name__ == "__main__":
    asyncio.run(main())
