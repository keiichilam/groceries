import { IStoreRepository, Item, Store, Inventory } from '../types';

export class InMemoryStoreRepository implements IStoreRepository {
  constructor(
    private readonly items: Item[],
    private readonly stores: Store[],
    private readonly inventory: Inventory[],
  ) {}

  getItems(): Item[] {
    return this.items;
  }

  getStores(): Store[] {
    return this.stores;
  }

  getInventory(): Inventory[] {
    return this.inventory;
  }
}
