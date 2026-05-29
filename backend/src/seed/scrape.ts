#!/usr/bin/env ts-node
import { getDb, closeDb } from '../db/database';
import { stores, items, inventory } from './tntMockData';

const args = process.argv.slice(2);
const chainArg = args.find((a) => a.startsWith('--chain='))?.split('=')[1]
  ?? (args[args.indexOf('--chain') + 1] ?? null);
const seedMock = args.includes('--seed-mock');

async function seedTnt(): Promise<void> {
  const db = getDb();

  const insertStore = db.prepare(
    'INSERT OR REPLACE INTO stores (id, name, lat, lng) VALUES (?, ?, ?, ?)',
  );
  const insertItem = db.prepare(
    'INSERT OR REPLACE INTO items (id, name, category) VALUES (?, ?, ?)',
  );
  const insertInventory = db.prepare(
    'INSERT OR REPLACE INTO inventory (store_id, item_id, price, in_stock) VALUES (?, ?, ?, ?)',
  );

  const seed = db.transaction(() => {
    for (const s of stores) insertStore.run(s.id, s.name, s.lat, s.lng);
    for (const i of items) insertItem.run(i.id, i.name, i.category);
    for (const inv of inventory) {
      insertInventory.run(inv.storeId, inv.itemId, inv.price, inv.inStock ? 1 : 0);
    }
  });

  seed();
  console.log(
    `Seeded T&T mock data: ${stores.length} stores, ${items.length} items, ${inventory.length} inventory rows.`,
  );
}

async function main(): Promise<void> {
  const chain = chainArg ?? 'all';

  if (chain === 'tnt' || chain === 'all') {
    if (chain === 'tnt' && !seedMock) {
      console.warn('T&T scraper not yet implemented. Use --seed-mock to load mock data.');
      console.warn('  npm run scrape -- --chain tnt --seed-mock');
    } else {
      await seedTnt();
    }
  }

  if (chain !== 'tnt' && chain !== 'all') {
    console.log(`Scraper for chain "${chain}" is not yet implemented.`);
  }

  if (chain === 'all' && !seedMock) {
    console.log('Live scrapers (walmart, safeway, saveon) are not yet implemented (Phase 2).');
  }

  closeDb();
}

main().catch((err) => {
  console.error(err);
  closeDb();
  process.exit(1);
});
