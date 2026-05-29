import Database from 'better-sqlite3';
import path from 'path';

const DB_PATH = process.env.DB_PATH ?? path.join(__dirname, '../../groceries.db');

let _db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!_db) {
    _db = new Database(DB_PATH);
    _db.pragma('journal_mode = WAL');
    _db.pragma('foreign_keys = ON');
    applyMigrations(_db);
  }
  return _db;
}

function applyMigrations(db: Database.Database): void {
  db.exec(`
    CREATE TABLE IF NOT EXISTS stores (
      id   TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      lat  REAL NOT NULL,
      lng  REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS items (
      id       TEXT PRIMARY KEY,
      name     TEXT NOT NULL,
      category TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS inventory (
      store_id  TEXT    NOT NULL REFERENCES stores(id),
      item_id   TEXT    NOT NULL REFERENCES items(id),
      price     REAL    NOT NULL,
      in_stock  INTEGER NOT NULL DEFAULT 1,
      PRIMARY KEY (store_id, item_id)
    );
  `);
}

export function closeDb(): void {
  if (_db) {
    _db.close();
    _db = null;
  }
}
