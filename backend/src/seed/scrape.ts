#!/usr/bin/env ts-node
/**
 * CLI entry point for scraping.
 *
 * Usage:
 *   npm run scrape                              # scrape all live chains
 *   npm run scrape -- --chain walmart           # scrape one chain
 *   npm run scrape -- --chain tnt --seed-mock   # reset T&T to mock dataset
 */
import { getDb, closeDb } from '../db/database';
import { stores, items, inventory } from './tntMockData';
import { runChain } from '../scraper/runChain';
import { persistScraperOutput } from '../scraper/persist';

const LIVE_CHAINS = ['walmart', 'safeway', 'saveon', 'tnt'];

const args = process.argv.slice(2);
const chainArg =
  args.find((a) => a.startsWith('--chain='))?.split('=')[1] ??
  (args.includes('--chain') ? args[args.indexOf('--chain') + 1] : null);
const seedMock = args.includes('--seed-mock');

async function seedTnt(): Promise<void> {
  const db = getDb();
  const insertStore     = db.prepare('INSERT OR REPLACE INTO stores (id, name, lat, lng) VALUES (?, ?, ?, ?)');
  const insertItem      = db.prepare('INSERT OR REPLACE INTO items (id, name, category) VALUES (?, ?, ?)');
  const insertInventory = db.prepare('INSERT OR REPLACE INTO inventory (store_id, item_id, price, in_stock) VALUES (?, ?, ?, ?)');

  db.transaction(() => {
    for (const s of stores)    insertStore.run(s.id, s.name, s.lat, s.lng);
    for (const i of items)     insertItem.run(i.id, i.name, i.category);
    for (const inv of inventory) insertInventory.run(inv.storeId, inv.itemId, inv.price, inv.inStock ? 1 : 0);
  })();

  console.log(`Seeded T&T mock data: ${stores.length} stores, ${items.length} items, ${inventory.length} inventory rows.`);
}

async function scrapeChain(chain: string): Promise<void> {
  console.log(`Scraping ${chain}...`);
  const output = await runChain(chain);
  const counts = persistScraperOutput(output);
  console.log(`  ${chain}: persisted ${counts.stores} stores, ${counts.inventory} inventory rows.`);
}

async function main(): Promise<void> {
  const chain = chainArg ?? 'all';

  if (seedMock) {
    if (chain === 'tnt' || chain === 'all') {
      await seedTnt();
    }
    if (chain !== 'tnt') {
      console.warn('--seed-mock only applies to --chain tnt.');
    }
    closeDb();
    return;
  }

  const targets = chain === 'all' ? LIVE_CHAINS : [chain];

  for (const c of targets) {
    try {
      await scrapeChain(c);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      console.error(`  ${c}: FAILED — ${msg}`);
    }
  }

  closeDb();
}

main().catch((err) => {
  console.error(err);
  closeDb();
  process.exit(1);
});
