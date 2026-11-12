"""Product identities on independent sites and shared project hosting.

A shared host is not a product identity. Recognizing a repository URL also does
not establish that its contents are a usable AI product; publication requires
the discovery pipeline's source-backed, project-specific verification record.
"""
import re
from urllib.parse import urlsplit


SHARED_PRODUCT_HOSTS = frozenset({'github.com', 'huggingface.co'})
_GITHUB_ROUTES = frozenset({
    'about', 'account', 'apps', 'codespaces', 'collections', 'contact', 'copilot',
    'customer-stories', 'dashboard', 'discussions', 'education', 'enterprise',
    'events', 'explore', 'features', 'issues', 'join', 'login', 'marketplace',
    'new', 'notifications', 'orgs', 'organizations', 'pricing', 'pulls',
    'readme', 'resources', 'search', 'security', 'sessions', 'settings', 'site',
    'solutions', 'sponsors', 'team', 'topics',
    'trending', 'users',
})
_HF_ROUTES = frozenset({
    'apps', 'blog', 'chat', 'collections', 'datasets', 'docs', 'enterprise',
    'hardware', 'join', 'learn', 'login', 'models', 'organizations', 'papers',
    'pricing', 'search', 'settings', 'spaces', 'tasks',
})
_SEGMENT = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]*$')


def _parts(value):
    raw = str(value or '').strip()
    if raw and '://' not in raw and '.' in raw:
        raw = 'https://' + raw
    try:
        parsed = urlsplit(raw)
        if parsed.scheme.lower() not in {'http', 'https'} or parsed.username or parsed.password:
            return None, ''
        host = (parsed.hostname or '').lower().removeprefix('www.')
        if not host:
            return None, ''
        return parsed, host
    except ValueError:
        return None, ''


def is_shared_host(url):
    return _parts(url)[1] in SHARED_PRODUCT_HOSTS


def hosted_project_key(url):
    """Recognize only project roots, never profiles, search, topics or files."""
    parsed, host = _parts(url)
    if host not in SHARED_PRODUCT_HOSTS:
        return ''
    try:
        if parsed.port not in (None, 80, 443):
            return ''
    except ValueError:
        return ''
    segments = parsed.path.strip('/').split('/')
    if any(not _SEGMENT.fullmatch(part) or part in {'.', '..'} for part in segments):
        return ''
    if host == 'github.com':
        if len(segments) != 2 or segments[0].lower() in _GITHUB_ROUTES:
            return ''
        owner, repo = segments
        if repo.endswith('.git'):
            repo = repo[:-4]
        if not repo:
            return ''
        return f'{host}/{owner.lower()}/{repo.lower()}'
    # A Space may be a usable app or merely a research demo. Evidence decides.
    if len(segments) == 3 and segments[0] == 'spaces':
        return host + '/' + '/'.join(segments)
    if len(segments) == 2 and segments[0].lower() not in _HF_ROUTES:
        return host + '/' + '/'.join(segments)
    return ''


def product_identity_key(url):
    """Identity for exclusions/discovery: site host or exact shared project."""
    parsed, host = _parts(url)
    if not host:
        return ''
    if host in SHARED_PRODUCT_HOSTS:
        # Keep non-project references (e.g. /features/copilot) scoped to their
        # page too. They must never turn an entire hosting service into a leader.
        return hosted_project_key(url) or host + parsed.path.rstrip('/')
    return host


def catalog_url_key(url):
    """Preserve existing catalog keys; shared hosts use the complete project."""
    parsed, host = _parts(url)
    if not host:
        return ''
    if host in SHARED_PRODUCT_HOSTS:
        return product_identity_key(url)
    first = parsed.path.strip('/').split('/')[0]
    return f'{host}/{first}' if len(first) > 1 else host


def is_verified_hosted_product(product):
    """Require the pipeline's explicit usable-product and identity evidence.

    This record is written only after source-quote, project-link and live
    identity checks. It is provenance, not an independent product-quality test.
    """
    key = hosted_project_key(product.get('website'))
    extra = product.get('extra')
    record = extra.get('hosted_project_verification') if isinstance(extra, dict) else None
    if not key or not isinstance(record, dict):
        return False
    quote = record.get('usage_quote')
    source = str(product.get('source_url') or '').strip()
    source_parts, source_host = _parts(source)
    return bool(
        record.get('verified') is True
        and record.get('project_key') == key
        and source_parts and source_host
        and record.get('source_url') == source
        and isinstance(quote, str) and len(quote.strip()) >= 16
    )
