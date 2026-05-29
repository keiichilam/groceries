"""Shared utilities for all chain scrapers."""
import asyncio
import hashlib
import json
import os
import random
import re
import sys
from typing import Any

SCRAPE_DELAY_MS = int(os.environ.get("SCRAPE_DELAY_MS", "1500"))
METRO_VAN_POSTAL = "V5H 1L3"  # Burnaby — covers all four target areas

FRUITS_VEG_KEYWORDS = {
    "fruit", "vegetable", "veg", "produce", "berry", "berries",
    "mushroom", "herb", "root", "taro", "yam", "mango", "durian",
    "lychee", "dragon fruit", "bok choy", "gai lan", "yu choy",
    "melon", "lotus", "radish", "onion", "ginger", "lemongrass",
    "cilantro", "bamboo", "broccoli", "napa", "tomato", "apple",
    "pear", "grape", "cherry", "blueberry", "strawberry", "banana",
}


async def delay(extra_ms: int = 0) -> None:
    ms = SCRAPE_DELAY_MS + extra_ms + random.randint(0, 500)
    await asyncio.sleep(ms / 1000)


def make_item_id(chain: str, name: str) -> str:
    """Stable ID: chain prefix + first 8 chars of sha256(normalized name)."""
    normalized = re.sub(r"[^a-z0-9]", "-", name.lower().strip())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    h = hashlib.sha256(normalized.encode()).hexdigest()[:8]
    slug = normalized[:30].rstrip("-")
    return f"{chain}-{slug}-{h}"


def is_produce(name: str, category: str) -> bool:
    """Rough filter: keep only fruit/veg adjacent items."""
    text = (name + " " + category).lower()
    return any(kw in text for kw in FRUITS_VEG_KEYWORDS)


def output(data: dict[str, Any]) -> None:
    json.dump(data, sys.stdout, ensure_ascii=False)
    sys.stdout.flush()


def error_exit(msg: str) -> None:
    print(json.dumps({"error": msg}), file=sys.stderr)
    sys.exit(1)


async def dismiss_overlays(page: Any) -> None:
    """Try to close common cookie/consent banners."""
    selectors = [
        "button[id*='accept']",
        "button[aria-label*='accept' i]",
        "button[aria-label*='close' i]",
        "#onetrust-accept-btn-handler",
        "[data-testid='cookie-accept']",
        "button:has-text('Accept')",
        "button:has-text('Accept All')",
        "button:has-text('Close')",
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=1500):
                await btn.click()
                await asyncio.sleep(0.5)
                break
        except Exception:
            pass
