import cron from 'node-cron';
import { runChain } from './runChain';
import { persistScraperOutput } from './persist';

const CHAINS = ['walmart', 'safeway', 'saveon', 'tnt'];
const CRON_SCHEDULE = process.env.SCRAPE_CRON ?? '0 3 * * *'; // 03:00 daily

async function scrapeAll(): Promise<void> {
  console.log('[scheduler] starting daily scrape run...');
  const results: string[] = [];

  for (const chain of CHAINS) {
    try {
      console.log(`[scheduler] scraping ${chain}...`);
      const output = await runChain(chain);
      const counts = persistScraperOutput(output);
      results.push(`${chain}: ${counts.stores} stores, ${counts.inventory} inventory rows`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      console.error(`[scheduler] ${chain} failed: ${msg}`);
      results.push(`${chain}: FAILED`);
    }
  }

  console.log('[scheduler] scrape run complete:');
  results.forEach((r) => console.log(`  ${r}`));
}

export function startScheduler(): void {
  if (!cron.validate(CRON_SCHEDULE)) {
    console.error(`[scheduler] invalid cron expression: ${CRON_SCHEDULE}`);
    return;
  }
  cron.schedule(CRON_SCHEDULE, () => {
    scrapeAll().catch((err) => console.error('[scheduler] unhandled error:', err));
  });
  console.log(`[scheduler] daily scrape scheduled at cron "${CRON_SCHEDULE}"`);
}
