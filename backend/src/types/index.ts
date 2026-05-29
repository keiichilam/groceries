export interface Item {
  id: string;
  name: string;
  category: string;
}

export interface Store {
  id: string;
  name: string;
  lat: number;
  lng: number;
}

export interface Inventory {
  storeId: string;
  itemId: string;
  price: number;
  inStock: boolean;
}

export interface RouteStop {
  store: Store;
  itemsToBuy: string[];
  distanceFromPrev: number; // km; first stop = distance from user's starting location
}

export interface RouteRecommendation {
  stops: RouteStop[];
  totalDistance: number; // km
  totalStops: number;
  score: number;
  weight: number;
  missingItems: string[];
}

export interface OptimizeRequest {
  itemIds: string[];
  userLat: number;
  userLng: number;
  weight?: number; // 0–1; default 0.4
}

export interface IStoreRepository {
  getItems(): Item[];
  getStores(): Store[];
  getInventory(): Inventory[];
}
