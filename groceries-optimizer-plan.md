# Groceries Optimizer Implementation Plan

## Objective
Build a full-stack web application that allows users to create a shopping list and recommends the optimal route across multiple supermarkets to acquire all items. The route is scored by a weighted combination of total travel distance and a distance-equivalent stop penalty; the default weight favors fewer stops but users can adjust the balance.

## Architecture & Tech Stack
- **Architecture**: Full-Stack
- **Frontend**: React (TypeScript)
  - **Styling**: Vanilla CSS (focus on rich aesthetics, gradients, clean layout).
  - **Mapping**: React-Leaflet for interactive map visualization.
- **Backend**: Node.js (Express) with TypeScript.
  - **Port**: `3001` (backend), `3000` (frontend dev server).
  - **CORS**: Enable CORS on the backend for `http://localhost:3000` in development.
  - **Data**: SQLite database (via `better-sqlite3`) used as the persistent cache for scraped data and as the source of truth for the optimizer. Seeded initially from the T&T mock dataset; overwritten/merged on each scrape run. Keep all data access behind a repository interface (`IStoreRepository`) so the optimizer never touches the database directly.
  - **Scraping**: [Camoufox](https://camoufox.com) (hardened Firefox with fingerprint spoofing) to reduce the likelihood of bot detection. Camoufox is a Python package (`pip install camoufox`); the Node.js scraper spawns it as a child process and communicates over CDP (Chrome DevTools Protocol) using Playwright's `connect` API. Python 3.10+ is therefore a dev dependency. If Camoufox is unavailable in the environment, fall back to `playwright-extra` with `puppeteer-extra-plugin-stealth` on Firefox. Runs as a separate CLI script (`npm run scrape`) and on a configurable schedule (default: every 24 h via `node-cron`). The Express server starts without waiting for a scrape; it serves whatever is in SQLite.

## Example Domain: T&T Supermarket (Canada)
The mock dataset is modelled after **T&T Supermarket**, a Canadian Asian grocery chain. Reference category: [Fruits & Vegetables](https://www.tntsupermarket.com/eng/product-categories/tt-fruits-vegetables.html?isRealCate=true). Products and prices below are sourced directly from the live site.

### Mock Stores (T&T branches + one Superstore for contrast)
| id | name | city | lat | lng |
|----|------|------|-----|-----|
| tnt-metrotown | T&T Supermarket Metrotown | Burnaby, BC | 49.2276 | -122.9998 |
| tnt-richmond | T&T Supermarket Richmond | Richmond, BC | 49.1666 | -123.1336 |
| tnt-downtown | T&T Supermarket Downtown | Vancouver, BC | 49.2827 | -123.1207 |
| superstore-bby | Real Canadian Superstore Burnaby | Burnaby, BC | 49.2488 | -122.9805 |

### Mock Item Catalog (Fruits & Vegetables — real T&T products)
| id | name | category |
|----|------|----------|
| F01 | Fresh Durian (7lbs) | Exotic Fruit |
| F02 | Specialty Lychee (2lb) | Exotic Fruit |
| F03 | Dragon Fruit (2.6lb) | Exotic Fruit |
| F04 | Red Dragon Fruit (1.5lbs) | Exotic Fruit |
| F05 | Sun Mango (2.5lb) | Tropical Fruit |
| F06 | Fresh Banana (~3lbs) | Tropical Fruit |
| F07 | Fuji Apple (2.8lbs) | Fruit |
| F08 | Asian Golden Pear (2.8lbs) | Fruit |
| F09 | Seedless Green Grape (~2.5lb) | Fruit |
| F10 | Cherry (2lb) | Fruit |
| F11 | Blueberry | Fruit |
| F12 | Strawberry (1lb) | Fruit |
| V01 | Shanghai Bok Choy (1.5lb) | Asian Vegetables |
| V02 | Gai Lan (~1.5lb) | Asian Vegetables |
| V03 | Yu Choy (~1.5lb) | Asian Vegetables |
| V04 | Bitter Melon (1.5lb) | Asian Vegetables |
| V05 | Lotus Root (1.5lb) | Asian Vegetables |
| V06 | Large Taro (~3lb) | Root Vegetables |
| V07 | Japanese Sweet Potato / Yam (2.5lb) | Root Vegetables |
| V08 | Hawaii Purple Sweet Potato / Yam (2.5lb) | Root Vegetables |
| V09 | White Radish (~2.5lb) | Root Vegetables |
| V10 | Green Onion (1bunch) | Aromatics |
| V11 | Ginger (1lb) | Aromatics |
| V12 | Lemon Grass (2-3pcs) | Herbs |
| V13 | Cilantro (1bunch) | Herbs |
| V14 | Bamboo Shoot (1.5lb) | Asian Vegetables |
| M01 | Organic Enoki Mushroom (150g) | Mushrooms |
| M02 | Shiitake Mushrooms (1.6lbs) | Mushrooms |
| M03 | Korean King Oyster Mushroom (300g) | Mushrooms |
| FZ01 | T&T Durian (454g) | Frozen |
| FZ02 | Frozen Golden Pillow Durian (8lb) | Frozen |
| FZ03 | Vefa Frozen Lemongrass (250g) | Frozen |
| SS1 | Vine Tomatoes (1.5lb) | Vegetables |
| SS2 | Crown Broccoli (1.5lb) | Vegetables |
| SS3 | Napa (~5lb) | Vegetables |

### Mock Inventory (partial — drives interesting routing decisions)
Specialty/exotic items are exclusive to specific T&T branches; everyday produce overlaps; frozen items are T&T-only; mainstream veg is also at Superstore.

| storeId | itemId | price (CAD) | inStock |
|---------|--------|-------------|---------|
| tnt-metrotown | F01 | 13.88 | true |
| tnt-metrotown | F02 | 3.99 | true |
| tnt-metrotown | F03 | 2.99 | true |
| tnt-metrotown | F07 | 2.29 | true |
| tnt-metrotown | F09 | 4.99 | true |
| tnt-metrotown | F11 | 3.98 | true |
| tnt-metrotown | V01 | 1.99 | true |
| tnt-metrotown | V02 | 2.29 | true |
| tnt-metrotown | V04 | 1.98 | true |
| tnt-metrotown | V05 | 2.49 | true |
| tnt-metrotown | V10 | 0.63 | true |
| tnt-metrotown | V11 | 1.99 | true |
| tnt-metrotown | M01 | 2.99 | true |
| tnt-metrotown | M02 | 3.88 | true |
| tnt-metrotown | FZ01 | 16.99 | true |
| tnt-metrotown | FZ02 | 5.99 | true |
| tnt-richmond | F01 | 13.88 | true |
| tnt-richmond | F04 | 5.88 | true |
| tnt-richmond | F05 | 5.99 | true |
| tnt-richmond | F06 | 0.89 | true |
| tnt-richmond | F08 | 1.69 | true |
| tnt-richmond | V03 | 1.68 | true |
| tnt-richmond | V06 | 1.99 | true |
| tnt-richmond | V07 | 2.88 | true |
| tnt-richmond | V08 | 5.99 | true |
| tnt-richmond | V12 | 1.99 | true |
| tnt-richmond | V14 | 6.99 | true |
| tnt-richmond | M02 | 3.88 | true |
| tnt-richmond | M03 | 3.99 | true |
| tnt-richmond | FZ02 | 5.99 | true |
| tnt-richmond | FZ03 | 1.34 | true |
| tnt-downtown | F02 | 3.99 | true |
| tnt-downtown | F10 | 9.99 | true |
| tnt-downtown | F12 | 6.99 | true |
| tnt-downtown | V01 | 1.99 | true |
| tnt-downtown | V09 | 1.09 | true |
| tnt-downtown | V10 | 0.63 | true |
| tnt-downtown | V11 | 1.99 | true |
| tnt-downtown | V13 | 1.99 | true |
| tnt-downtown | M01 | 2.99 | true |
| tnt-downtown | M03 | 3.99 | true |
| tnt-downtown | FZ01 | 16.99 | true |
| superstore-bby | F07 | 2.49 | true |
| superstore-bby | F09 | 5.49 | true |
| superstore-bby | F11 | 4.49 | true |
| superstore-bby | F12 | 5.99 | true |
| superstore-bby | SS1 | 2.99 | true |
| superstore-bby | SS2 | 2.49 | true |
| superstore-bby | SS3 | 1.99 | true |
| superstore-bby | V10 | 0.99 | true |
| superstore-bby | V11 | 2.29 | true |

## Web Scraping Layer

### Target Store Chains (Metro Vancouver)
In addition to T&T (mocked), the scraper targets:

| Chain | Site | Notes |
|-------|------|-------|
| Walmart Canada | walmart.ca | SPA; intercept internal product API calls via CDP network interception |
| Safeway | safeway.ca | Sobeys-powered SPA; requires postal-code session to see local pricing |
| Save-On-Foods | saveonfoods.com | React SPA; category pages load products via XHR |
| T&T Supermarket | tntsupermarket.com | Static-ish pages; use Camoufox for consistency with other chains |

### Store Locator Scraping
Before scraping inventory, the scraper resolves each chain's Metro Vancouver branches:
- For each chain, call the store-locator endpoint or page (e.g. `walmart.ca/store-finder`) with a Metro Vancouver postal code (V5K) to get branch names, addresses, and coordinates (lat/lng).
- Persist results to the `stores` table. Existing T&T mock entries are preserved (or overwritten if the same `id` is scraped).
- Store IDs are slugified from `{chain}-{city}-{branch}` (e.g. `walmart-burnaby-metrotown`).

### Product & Inventory Scraping
For each branch, scrape the Fruits & Vegetables category (and its sub-categories) to match the T&T item scope:
1. Navigate to the chain's Fruits & Vegetables category page, selecting the branch/store so prices and stock are store-specific.
2. Paginate through all products; for each product record: `name`, `price`, `inStock` (inferred from "Add to Cart" availability), and any available unit/weight descriptor.
3. Persist to `items` and `inventory` tables. Items are identified by a content-hash of `{chain}-{normalizedName}` to survive re-scrapes.

### Product Normalization
Products across chains won't share names (e.g. T&T "Shanghai Bok Choy" vs Safeway "Bok Choy"). Strategy:
- Scraped products are stored in their **native form** (no cross-chain ID merging). Each chain's items are independent entries in the `items` table.
- The frontend autocomplete shows all items from all chains; search is by name. The user picks what they want without needing to know which store carries it.
- Cross-chain equivalence (e.g. "any bok choy") is a future enhancement; do not implement it now.

### Scraping Robustness
- **Anti-detection**: Camoufox handles canvas fingerprint spoofing, locale randomisation, and realistic browser headers automatically. Do not override its user-agent or fingerprint settings.
- **Rate limiting**: configurable `SCRAPE_DELAY_MS` (default 1500 ms) between page requests per chain; configurable `SCRAPE_DELAY_BETWEEN_CHAINS_MS` (default 5000 ms).
- **Failure handling**: if a chain's scrape fails partway through, log the error and continue with other chains. Stale SQLite data from the previous successful run remains valid until the next successful scrape.
- **Fallback**: if `camoufox` Python process cannot be spawned (missing Python, install error), log a warning and retry with `playwright-extra` + stealth plugin on Firefox.
- **ToS / robots.txt**: scraping is for personal/educational use only. Do not distribute scraped data or run at aggressive rates.

### Scrape CLI
```
npm run scrape              # scrape all chains
npm run scrape -- --chain walmart   # scrape one chain
npm run scrape -- --chain tnt --seed-mock  # reset T&T to mock dataset
```

## Core Features & Logic
1. **Shopping List Manager**: UI to add/remove grocery items.
2. **Store & Inventory Mocking**: A robust backend dataset of local stores, their coordinates (lat/lng), and their available inventory with prices.
3. **Advanced Routing Optimization**:
   - The algorithm uses a joint optimizer: enumerate all **inclusion-minimal** subsets of stores that together cover all available requested items, up to a configurable cap of `MAX_STORES = 5`. A subset is inclusion-minimal if removing any single store from it leaves at least one item uncovered (i.e., no proper sub-subset is itself a valid cover). For each minimal subset, enumerate every store order starting from the user's location and keep the shortest open path. The route ends at the last store; it does not include a return trip to the user's starting point.
   - Score each candidate with `weight * totalDistanceKm + (1 - weight) * totalStops * STOP_PENALTY_KM`, where `STOP_PENALTY_KM = 10`. Expressing both terms in distance-equivalent units makes the slider behavior predictable. Return the lowest-scoring candidate, breaking ties by fewer stops, then shorter distance, then lexicographically by ordered store IDs.
   - Assign each requested item to the cheapest selected store that stocks it. If multiple selected stores have the same price, assign it to the earliest store in the route. Price determines the shopping breakdown within the selected route; it is not an optimization objective.
   - Exhaustively enumerating store orders is acceptable while `MAX_STORES = 5`. If available requested items cannot be covered within that cap, return `422` with error code `STORE_CAP_EXCEEDED`. Before increasing the cap or adding substantially more stores, replace permutation enumeration with a documented approximation and add performance benchmarks.
   - Distance is computed with the **Haversine formula** (straight-line). A routing API can replace this later, but the scoring and selection logic must not depend on which distance function is used.
   - If a known catalog item is unavailable at every store in the dataset, collect its ID in a `missingItems` array and continue optimizing the available items rather than causing a failure.
4. **Interactive Map Itinerary**:
   - The frontend will display an interactive map showing the user's starting point, the recommended stores as markers, and lines connecting them to visualize the route.
   - A text-based breakdown of which items to buy at each specific store.

## Data Model (Proposed)
- `Item`: { id, name, category }
- `Store`: { id, name, lat, lng }
- `Inventory`: { storeId, itemId, price, inStock: boolean }
- `RouteRecommendation`: { stops: [{ store, itemsToBuy, distanceFromPrev }], totalDistance, totalStops, score, weight, missingItems: string[] }
  - `stops` is the single ordered source of truth; the frontend derives map polylines and the text breakdown from the same array.
  - `totalDistance` and `distanceFromPrev` are measured in kilometres. The route is an open path ending at the final store.
  - `distanceFromPrev` for the **first stop** is the distance from the user's starting location (not zero and not omitted).
  - `itemsToBuy` contains item IDs assigned using the cheapest-selected-store rule above.
  - `weight` echoes back the weight value used for this optimization (useful for the frontend to display or replay results).
- `OptimizeRequest`: { itemIds: string[], userLat: number, userLng: number, weight?: number }
  - `weight` is 0–1, where 1 = minimize distance only and 0 = minimize stops only. Default: 0.4, which favors fewer stops.

## API Validation & Edge Cases
- Reject malformed requests with `400`, including an empty `itemIds` array, unknown catalog IDs, non-finite or out-of-range coordinates, non-finite weights, and weights outside `0..1`.
- Deduplicate repeated item IDs before optimization.
- Treat known catalog items with no in-stock inventory as `missingItems`, continue optimizing the remaining items, and return an empty `stops` array if every requested item is missing.
- Use browser geolocation when permission is granted. If it is unavailable or denied, initialize the frontend at Vancouver City Hall (`49.2609`, `-123.1139`) and allow the user to place or move the starting-point marker on the map.
- Return `422` with error code `STORE_CAP_EXCEEDED` if available requested items cannot be covered within `MAX_STORES`.

## Phased Implementation Plan

### Phase 1: Project Initialization & Foundation
- [ ] Track implementation status in `tasks/todo.md`, using the phased checklist below as the source of truth.
- [ ] Setup React frontend and Node.js backend repositories/folders.
- [ ] Define shared TypeScript interfaces (`Item`, `Store`, `Inventory`, `RouteRecommendation`, `OptimizeRequest`, `IStoreRepository`).
- [ ] Initialize SQLite with `better-sqlite3`; define and apply schema migrations for `stores`, `items`, `inventory` tables.
- [ ] Implement `SqliteStoreRepository` satisfying `IStoreRepository`; implement `InMemoryStoreRepository` for unit tests.
- [ ] Seed SQLite with the T&T mock dataset defined above (4 stores, 35 items, 51 inventory rows) via `npm run scrape -- --chain tnt --seed-mock`.

### Phase 2: Web Scraper Implementation
- [ ] Install Python 3.10+, `camoufox` (`pip install camoufox`), and `playwright` npm package for CDP `connect` API. Document setup in `README.md`.
- [ ] Implement a `BrowserFactory` module that spawns Camoufox and returns a Playwright `Browser` via CDP; falls back to `playwright-extra` + stealth on Firefox if Camoufox is unavailable.
- [ ] Implement store-locator scraper for each chain (Walmart, Safeway, Save-On-Foods, T&T) to populate the `stores` table with real Metro Vancouver branches and coordinates.
- [ ] Implement product/inventory scraper for each chain's Fruits & Vegetables category, persisting to `items` and `inventory` tables.
- [ ] Wire up `node-cron` to schedule daily scrapes; expose `npm run scrape` CLI with `--chain` and `--seed-mock` flags.
- [ ] Verify scraped data by spot-checking a sample of items and prices against the live sites.

### Phase 3: Core Algorithm Development (Backend)
- [ ] Implement the optimization engine in the backend, reading from `IStoreRepository`.
- [ ] Create endpoints:
  - `GET /api/items` — returns the full item catalog (id, name, category) so the frontend can resolve names to IDs.
  - `POST /api/optimize-route` — accepts `OptimizeRequest`, returns `RouteRecommendation`.
- [ ] Write unit tests for the optimization logic, including:
  - All items at exactly one store (e.g. [F03, V02, V05] → tnt-metrotown only).
  - Items split across stores (e.g. [F04, V08, FZ03] → only tnt-richmond; [F10, V13] → only tnt-downtown; combining them forces both).
  - Items exclusive to one branch (e.g. V08 Hawaii Purple Sweet Potato only at tnt-richmond; F10 Cherry only at tnt-downtown).
  - Mainstream items available at Superstore but also at T&T (e.g. F09 grape, V10 green onion) — router should prefer fewer stops over cheapest price.
  - A separate small fixture where sequential greedy Set Cover + route ordering selects a worse scored route than joint subset and route optimization. Assert both routes and scores explicitly. Use the following fixture (inject via the repository interface, bypassing the main 4-store dataset):
    - User: `(49.25, -123.10)`; weight `0.4`
    - **store-dominant** `(49.52, -123.10)` stocks: `P, Q, R, S` — ~30 km north of user
    - **store-complement** `(49.52, -122.99)` stocks: `T, U` — ~30 km north, ~7 km east of dominant
    - **store-near-a** `(49.259, -123.10)` stocks: `P, Q, T` — ~1 km north of user
    - **store-near-b** `(49.268, -123.10)` stocks: `R, S, U` — ~2 km north of user
    - Request items: `[P, Q, R, S, T, U]`
    - Greedy set cover (maximize new items covered per step, tie-break by store ID): picks `store-dominant` (4 items), then `store-complement` (2 remaining). Route: user→dominant→complement, ~37 km total.
    - Joint optimal: `{store-near-a, store-near-b}` covers all 6 items, route user→near-a→near-b, ~2 km total.
    - Assert that joint score < greedy score (compute exact values via Haversine); assert joint route stops are `[store-near-a, store-near-b]`.
  - Tie-breaking: craft a fixture where two candidate routes have identical scores; verify the response breaks the tie by fewer stops first, then shorter total distance, then lexicographic store ID order.
  - A known catalog item not in any store's inventory → verify `missingItems` is populated, available items are still optimized, and the response is not a 500.
  - Duplicate IDs, unknown IDs, empty lists, invalid coordinates, and invalid weights.
  - A crafted fixture that exceeds `MAX_STORES` → verify a `422 STORE_CAP_EXCEEDED` response. Trigger this by temporarily setting `MAX_STORES = 2` and requesting items that require 3 or more stores from the main dataset (e.g. `[F03, V08, F10]` which span tnt-metrotown, tnt-richmond, and tnt-downtown).

### Phase 4: Frontend Development
- [ ] Build the UI layout (Shopping List Sidebar + Main Map Area).
- [ ] Implement the shopping list form: fetch the item catalog from `GET /api/items`, provide autocomplete/search by **item name** so users never see or type raw IDs. Resolve the selected name to its ID before sending the `OptimizeRequest`.
- [ ] Add a weight slider (distance vs. stops tradeoff) in the UI, defaulting to 0.4.
- [ ] Integrate React-Leaflet to render the base map and user location. Use browser geolocation when available, fall back to Vancouver City Hall (`49.2609`, `-123.1139`), and allow the starting-point marker to be moved.

### Phase 5: Integration & Polish
- [ ] Connect frontend to the backend optimization endpoint, passing item IDs (resolved from catalog) and the weight slider value.
- [ ] Derive map polylines and stop markers from the single `stops` array in the response.
- [ ] Display `missingItems` prominently if the response includes any (e.g., a warning banner).
- [ ] Apply rich styling (Vanilla CSS) for a modern, clean look.

## Verification
- [ ] Run `npm run scrape` and confirm all four chains produce non-empty `stores` and `inventory` rows in SQLite; spot-check at least 3 items per chain against the live site for price/stock accuracy.
- [ ] Confirm `GET /api/items` returns items from all scraped chains, not just T&T.
- [ ] Test optimization with items exclusive to specific branches (e.g. Hawaii Purple Sweet Potato + Cherry → must visit tnt-richmond + tnt-downtown).
- [ ] Test that joint subset and route optimization produces a better score than sequential greedy Set Cover + route ordering on a crafted dataset where they diverge.
- [ ] Test the unsatisfiable case: request an item not in any store's inventory and verify `missingItems` is returned (not a 500).
- [ ] Verify map polylines and the text stop breakdown reflect the same `stops` order.
- [ ] Verify the weight slider changes the returned route on a crafted fixture where the objectives diverge (e.g., weight=0 prefers fewer stops, weight=1 prefers shorter distance).
- [ ] Verify browser geolocation success, denied-permission fallback, and draggable starting-point behavior.
- [ ] Ensure responsive design and visually appealing UI.
