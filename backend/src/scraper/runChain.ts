import { spawn } from 'child_process';
import path from 'path';
import type { ScraperOutput } from './types';

const SCRAPERS_DIR = path.join(__dirname, '../../scrapers');

const CHAIN_SCRIPTS: Record<string, string> = {
  walmart: 'walmart.py',
  safeway: 'safeway.py',
  saveon:  'saveon.py',
  tnt:     'tnt.py',
};

export async function runChain(chain: string): Promise<ScraperOutput> {
  const script = CHAIN_SCRIPTS[chain];
  if (!script) {
    throw new Error(`Unknown chain: "${chain}". Valid chains: ${Object.keys(CHAIN_SCRIPTS).join(', ')}`);
  }

  const scriptPath = path.join(SCRAPERS_DIR, script);
  const env = {
    ...process.env,
    SCRAPE_DELAY_MS: process.env.SCRAPE_DELAY_MS ?? '1500',
  };

  return new Promise((resolve, reject) => {
    let stdout = '';
    let stderr = '';

    const child = spawn('python3', [scriptPath], { env, cwd: SCRAPERS_DIR });

    child.stdout.on('data', (chunk: Buffer) => { stdout += chunk.toString(); });
    child.stderr.on('data', (chunk: Buffer) => {
      const line = chunk.toString();
      stderr += line;
      process.stderr.write(`[${chain}] ${line}`);
    });

    child.on('error', (err) => reject(new Error(`Failed to spawn python3: ${err.message}`)));

    child.on('close', (code) => {
      if (!stdout.trim()) {
        reject(new Error(`${chain} scraper produced no output. stderr:\n${stderr}`));
        return;
      }
      try {
        const result = JSON.parse(stdout) as ScraperOutput;
        if (result.error) {
          reject(new Error(`${chain} scraper error: ${result.error}`));
        } else {
          resolve(result);
        }
      } catch {
        reject(new Error(`${chain} scraper output was not valid JSON. code=${code}\nstdout: ${stdout.slice(0, 500)}`));
      }
    });
  });
}
