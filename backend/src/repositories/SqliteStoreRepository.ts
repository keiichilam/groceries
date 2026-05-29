import { IStoreRepository, Item, Store, Inventory } from '../types';
import { getDb } from '../db/database';

export class SqliteStoreRepository implements IStoreRepository {
  getItems(): Item[] {
    return getDb()
      .prepare('SELECT id, name, category FROM items ORDER BY id')
      .all() as Item[];
  }

  getStores(): Store[] {
    return getDb()
      .prepare('SELECT id, name, lat, lng FROM stores ORDER BY id')
      .all() as Store[];
  }

  getInventory(): Inventory[] {
    return (
      getDb()
        .prepare('SELECT store_id AS storeId, item_id AS itemId, price, in_stock AS inStock FROM inventory')
        .all() as Array<{ storeId: string; itemId: string; price: number; inStock: number }>
    ).map((row) => ({ ...row, inStock: row.inStock === 1 }));
  }
}
