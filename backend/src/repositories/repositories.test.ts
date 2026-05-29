import path from 'path';

// Point at the seeded test DB
process.env.DB_PATH = path.join(__dirname, '../../groceries.db');

import { SqliteStoreRepository } from './SqliteStoreRepository';
import { InMemoryStoreRepository } from './InMemoryStoreRepository';
import { closeDb } from '../db/database';
import type { Item, Store, Inventory } from '../types';

afterAll(() => closeDb());

describe('SqliteStoreRepository', () => {
  const repo = new SqliteStoreRepository();

  it('returns 35 items', () => {
    expect(repo.getItems()).toHaveLength(35);
  });

  it('returns 4 stores', () => {
    expect(repo.getStores()).toHaveLength(4);
  });

  it('returns 51 inventory rows', () => {
    expect(repo.getInventory()).toHaveLength(51);
  });

  it('items have required fields', () => {
    const item = repo.getItems()[0];
    expect(item).toHaveProperty('id');
    expect(item).toHaveProperty('name');
    expect(item).toHaveProperty('category');
  });

  it('stores have required fields including coordinates', () => {
    const store = repo.getStores()[0];
    expect(store).toHaveProperty('id');
    expect(store).toHaveProperty('name');
    expect(typeof store.lat).toBe('number');
    expect(typeof store.lng).toBe('number');
  });

  it('inventory inStock is a boolean', () => {
    const row = repo.getInventory()[0];
    expect(typeof row.inStock).toBe('boolean');
  });
});

describe('InMemoryStoreRepository', () => {
  const items: Item[] = [
    { id: 'A1', name: 'Apple', category: 'Fruit' },
    { id: 'B1', name: 'Banana', category: 'Tropical Fruit' },
  ];
  const stores: Store[] = [
    { id: 'store-a', name: 'Store A', lat: 49.25, lng: -123.1 },
  ];
  const inventory: Inventory[] = [
    { storeId: 'store-a', itemId: 'A1', price: 1.5, inStock: true },
    { storeId: 'store-a', itemId: 'B1', price: 0.5, inStock: false },
  ];

  const repo = new InMemoryStoreRepository(items, stores, inventory);

  it('returns injected items', () => {
    expect(repo.getItems()).toEqual(items);
  });

  it('returns injected stores', () => {
    expect(repo.getStores()).toEqual(stores);
  });

  it('returns injected inventory', () => {
    expect(repo.getInventory()).toEqual(inventory);
  });
});
