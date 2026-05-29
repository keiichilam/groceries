import crypto from 'crypto';
import { getDb } from '../db/database';
import type { ScraperOutput, ScrapedInventoryRow } from './types';

const insertStore = () =>
  getDb().prepare('INSERT OR REPLACE INTO stores (id, name, lat, lng) VALUES (?, ?, ?, ?)');

const insertItem = () =>
  getDb().prepare('INSERT OR REPLACE INTO items (id, name, category) VALUES (?, ?, ?)');

const insertInventory = () =>
  getDb().prepare(
    'INSERT OR REPLACE INTO inventory (store_id, item_id, price, in_stock) VALUES (?, ?, ?, ?)',
  );

function makeItemId(chain: string, name: string): string {
  const normalized = name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
  const hash = crypto.createHash('sha256').update(normalized).digest('hex').slice(0, 8);
  const slug = normalized.slice(0, 30).replace(/-$/, '');
  return `${chain}-${slug}-${hash}`;
}

export function persistScraperOutput(output: ScraperOutput): { stores: number; items: number; inventory: number } {
  const db = getDb();

  const upsertStore = insertStore();
  const upsertItem = insertItem();
  const upsertInv = insertInventory();

  let itemCount = 0;
  let invCount = 0;

  const run = db.transaction(() => {
    for (const store of output.stores) {
      upsertStore.run(store.id, store.name, store.lat, store.lng);
    }

    for (const row of output.inventory) {
      const itemId = makeItemId(output.chain, row.itemName);
      upsertItem.run(itemId, row.itemName, row.category);
      upsertInv.run(row.storeId, itemId, row.price, row.inStock ? 1 : 0);
      itemCount++;
      invCount++;
    }
  });

  run();

  return { stores: output.stores.length, items: itemCount, inventory: invCount };
}
