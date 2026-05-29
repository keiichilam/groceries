# Groceries Optimizer — TODO

## Phase 1: Project Initialization & Foundation ✅

- [x] Setup React frontend and Node.js backend directories
- [x] Define shared TypeScript interfaces: `Item`, `Store`, `Inventory`, `RouteRecommendation`, `OptimizeRequest`, `IStoreRepository`
- [x] Initialize SQLite with `better-sqlite3`; apply schema migrations for `stores`, `items`, `inventory` tables
- [x] Implement `SqliteStoreRepository` satisfying `IStoreRepository`
- [x] Implement `InMemoryStoreRepository` for unit tests
- [x] Seed SQLite with T&T mock dataset (4 stores, 35 items, 51 inventory rows) via `npm run scrape -- --chain tnt --seed-mock`

## Phase 2: Web Scraper Implementation

- [ ] Install Python 3.10+, `camoufox` (`pip install camoufox`), and `playwright` npm package; document setup in `README.md`
- [ ] Implement `BrowserFactory` module: spawns Camoufox via CDP; falls back to `playwright-extra` + stealth on Firefox
- [ ] Implement store-locator scraper for Walmart, Safeway, Save-On-Foods, T&T → populate `stores` table with Metro Vancouver branches and coordinates
- [ ] Implement product/inventory scraper for each chain's Fruits & Vegetables category → persist to `items` and `inventory` tables
- [ ] Wire up `node-cron` for daily scrapes; expose `npm run scrape` CLI with `--chain` and `--seed-mock` flags
- [ ] Spot-check ≥3 items per chain against live sites for price/stock accuracy

## Phase 3: Core Algorithm Development (Backend)

- [ ] Implement inclusion-minimal subset enumeration over stores
- [ ] Implement permutation-based route ordering with Haversine distance
- [ ] Implement scoring: `weight * totalDistanceKm + (1 - weight) * totalStops * 10`
- [ ] Implement cheapest-store item assignment with route-order tie-breaking
- [ ] Implement `missingItems` collection and graceful degradation
- [ ] Implement `STORE_CAP_EXCEEDED` (422) when required stores exceed `MAX_STORES = 5`
- [ ] Create `GET /api/items` endpoint
- [ ] Create `POST /api/optimize-route` endpoint with full request validation (400 on malformed input, deduplication)
- [ ] Write unit tests:
  - [ ] All items at one store: `[F03, V02, V05]` → `tnt-metrotown`
  - [ ] Items split across stores: `[F04, V08, FZ03]` → `tnt-richmond`; `[F10, V13]` → `tnt-downtown`; combined → both
  - [ ] Exclusive-branch items: V08 only at `tnt-richmond`, F10 only at `tnt-downtown`
  - [ ] Multi-chain overlap: `[F09, V10]` — router prefers fewer stops over cheapest price
  - [ ] Greedy-vs-joint fixture: assert `{store-near-a, store-near-b}` beats `{store-dominant, store-complement}` on score
  - [ ] Tie-breaking fixture: identical scores resolved by stops → distance → lexicographic store ID
  - [ ] `missingItems`: item in catalog but no inventory → populated, rest optimized, no 500
  - [ ] Duplicate IDs, unknown IDs, empty list, invalid coordinates, invalid weights → 400
  - [ ] `STORE_CAP_EXCEEDED`: `MAX_STORES = 2`, request `[F03, V08, F10]` → 422

## Phase 4: Frontend Development

- [ ] Build UI layout: Shopping List sidebar + Main Map area
- [ ] Fetch item catalog from `GET /api/items`; implement name-based autocomplete (IDs resolved internally)
- [ ] Add weight slider (0–1, default 0.4) with distance vs. stops label
- [ ] Integrate React-Leaflet: base map, user location marker (geolocation → fallback Vancouver City Hall `49.2609, -123.1139`), draggable start marker

## Phase 5: Integration & Polish

- [ ] Connect frontend to `POST /api/optimize-route`, passing resolved item IDs and weight
- [ ] Derive map polylines and stop markers from `stops` array in response
- [ ] Display `missingItems` warning banner when response includes any
- [ ] Apply Vanilla CSS styling: gradients, clean layout, modern look
- [ ] Verify responsive design

## Verification

- [ ] `npm run scrape` → all four chains produce non-empty `stores` and `inventory` rows; spot-check prices
- [ ] `GET /api/items` returns items from all scraped chains
- [ ] Hawaii Purple Sweet Potato + Cherry → route visits `tnt-richmond` + `tnt-downtown`
- [ ] Joint optimizer scores better than greedy on divergence fixture
- [ ] Missing item request → `missingItems` returned, no 500
- [ ] Map polylines and text breakdown match same `stops` order
- [ ] Weight slider changes route on fixture where objectives diverge
- [ ] Geolocation: success path, denied-permission fallback, draggable marker
- [ ] Responsive design and visual polish
