import express from 'express';
import cors from 'cors';
import { SqliteStoreRepository } from './repositories/SqliteStoreRepository';

const app = express();
const PORT = process.env.PORT ?? 3001;

app.use(cors({ origin: 'http://localhost:3000' }));
app.use(express.json());

const repo = new SqliteStoreRepository();

app.get('/api/items', (_req, res) => {
  res.json(repo.getItems());
});

app.listen(PORT, () => {
  console.log(`Backend running on http://localhost:${PORT}`);
});
