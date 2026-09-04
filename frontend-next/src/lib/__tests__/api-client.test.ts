import { afterEach, expect, it, vi } from 'vitest';
import { getProductById, getWeeklyTop } from '../api-client';

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
