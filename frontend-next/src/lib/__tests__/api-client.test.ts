import { afterEach, expect, it, vi } from 'vitest';
import { getDiscoveryPage, getProductById, getWeeklyTop } from '../api-client';

afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); });

it('surfaces an unavailable backend instead of an empty collection', async () => {
  vi.stubEnv('API_BASE_URL_SERVER', 'https://backend.example/api/v1');
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 503 })));
  await expect(getWeeklyTop()).rejects.toThrow();
});

it('treats a real missing product as not found', async () => {
  vi.stubEnv('API_BASE_URL_SERVER', 'https://backend.example/api/v1');
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 404 })));
  await expect(getProductById('missing')).resolves.toBeNull();
});

it('rejects corrupt API data instead of masking a contract failure', async () => {
  vi.stubEnv('API_BASE_URL_SERVER', 'https://backend.example/api/v1');
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json({ data: 'not an array' })));
  await expect(getWeeklyTop()).rejects.toThrow();
});

it('requests only a bounded discovery page and keeps numeric funding renderable', async () => {
  vi.stubEnv('API_BASE_URL_SERVER', 'https://backend.example/api/v1');
  const fetcher = vi.fn().mockResolvedValue(Response.json({
    data: [{ name: 'Autoheal', funding_total: 7900000 }],
    pagination: { offset: 36, limit: 36, total: 73, has_more: true },
  }));
  vi.stubGlobal('fetch', fetcher);
  const page = await getDiscoveryPage(36);
  expect(page.data[0].funding_total).toBe('7900000');
  expect(page.pagination.has_more).toBe(true);
  expect(fetcher).toHaveBeenCalledWith('https://backend.example/api/v1/products/discovery-feed?offset=36&limit=36',
    expect.objectContaining({ next: { revalidate: 60, tags: ['products'] } }));
});

it('does not silently terminate discovery when pagination is missing', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json({ data: [] })));
  await expect(getDiscoveryPage()).rejects.toThrow();
});
