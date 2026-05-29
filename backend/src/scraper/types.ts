export interface ScrapedStore {
  id: string;
  name: string;
  lat: number;
  lng: number;
  storeId?: string; // chain-internal store ID, used during scraping
}

export interface ScrapedInventoryRow {
  storeId: string;
  itemName: string;
  category: string;
  price: number;
  inStock: boolean;
}

export interface ScraperOutput {
  chain: string;
  stores: ScrapedStore[];
  inventory: ScrapedInventoryRow[];
  error?: string;
}
