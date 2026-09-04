/** Browsers use our own origin; only the server needs the Flask address. */
export function getServerApiBase(): string {
  const configured = (process.env.API_BASE_URL_SERVER || process.env.NEXT_PUBLIC_API_BASE_URL || '')
    .trim().replace(/^['"]|['"]$/g, '').replace(/\/+$/, '');
  const base = configured || (process.env.NODE_ENV === 'production'
    ? 'https://backend-seven-ecru-62.vercel.app/api/v1'
    : 'http://127.0.0.1:5000/api/v1');
  const url = new URL(base);
  if (!['https:', 'http:'].includes(url.protocol) || url.username || url.password || url.search || url.hash) {
    throw new Error('API_BASE_URL_SERVER must be an HTTP(S) API URL without credentials or query parameters.');
  }
  return base;
}

export const BROWSER_API_BASE = '/api/v1';
