import { getServerApiBase } from '@/lib/api-base';

export const runtime = 'nodejs';
export const maxDuration = 60;

async function proxy(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  if (!['products', 'search', 'chat', 'health'].includes(path[0]) || path.some(part => part === '.' || part === '..' || /[\\/]/.test(part))) {
    return Response.json({ success: false, message: 'Unknown API route.' }, { status: 404 });
  }
  try {
    const base = getServerApiBase();
    const suffix = path.map(encodeURIComponent).join('/') + (path[0] === 'search' && path.length === 1 ? '/' : '');
    const url = `${base}/${suffix}${new URL(request.url).search}`;
    const body = request.method === 'POST' ? await request.text() : undefined;
    if (body && new TextEncoder().encode(body).length > 24000) {
      return Response.json({ success: false, message: 'Request is too large.' }, { status: 413 });
    }
    const upstream = await fetch(url, {
      method: request.method,
      headers: {
        Accept: request.headers.get('accept') || 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': request.headers.get('user-agent') || 'WeeklyAI web',
        'X-Forwarded-For': request.headers.get('x-forwarded-for') || 'unknown',
      },
      body,
      cache: 'no-store',
      signal: AbortSignal.any([request.signal, AbortSignal.timeout(45000)]),
      redirect: 'error',
    });
    return new Response(upstream.body, {
      status: upstream.status,
      headers: {
        'Content-Type': upstream.headers.get('content-type') || 'application/json',
        'Cache-Control': 'no-store',
        ...(upstream.headers.has('retry-after') ? { 'Retry-After': upstream.headers.get('retry-after')! } : {}),
      },
    });
  } catch {
    return Response.json({ success: false, content: 'The product service is temporarily unavailable. Please retry.', error: 'SERVICE_UNAVAILABLE' }, { status: 503 });
  }
}

export const GET = proxy;
export const POST = proxy;
