"""Bounded, rotating searches and fair article allocation across discovery markets."""
from collections import defaultdict, deque
from datetime import datetime, timezone
from urllib.parse import urlsplit


MARKETS = {
    'us': ('United States', 'US'),
    'cn': ('中国', 'CN'),
    'eu': ('Europe', 'GB IE FR DE ES PT IT NL BE CH AT SE NO DK FI PL CZ EE LT LV RO GR UA'),
    'jp': ('日本', 'JP'),
    'kr': ('한국', 'KR'),
    'sea': ('Southeast Asia Singapore Indonesia Vietnam Thailand Malaysia Philippines', 'SG ID VN TH MY PH KH LA MM BN TL'),
    'other': ('emerging markets', 'CA AU NZ IN BR MX AR CL CO ZA NG KE EG AE SA IL TR'),
}
FEED_MARKETS = {
    'TechCrunch Startups': 'us', 'TechCrunch AI': 'us', 'TechCrunch Venture': 'us',
    'VentureBeat': 'us', '36kr': 'cn', 'QbitAI': 'cn', 'TMTPost': 'cn',
    'Leiphone': 'cn', 'iFanr': 'cn', 'Tech.eu': 'eu', 'Sifted': 'eu', 'BetaKit': 'other',
}
NICHES = [
    ('AI robotics edge devices agriculture manufacturing', 'AI workflow developer tools small business'),
    ('AI sensors assistive devices accessibility healthcare', 'AI education legal accounting local languages'),
    ('AI hardware energy logistics industrial inspection', 'open source AI privacy research vertical agents'),
    ('AI wearables audio medical devices', 'indie AI design audio productivity bootstrapped'),
    ('AI chips embedded vision drones', 'AI climate construction supply chain niche SaaS'),
]


def markets_for(region):
    # The existing CLI uses jp for both Japan and Korea.
    return list(MARKETS) if region == 'all' else ['jp', 'kr'] if region == 'jp' else [region]


def search_plan(region='all', product_type='mixed', now=None):
    now = now or datetime.now(timezone.utc)
    day = now.date().toordinal()
    hardware, software = NICHES[day % len(NICHES)]
    niche = hardware if product_type == 'hardware' or (product_type == 'mixed' and day % 5 < 2) else software
    # These are search targets, never inferred company nationality.
    emerging = ['India AI startup', 'Latin America IA startup Brasil México',
                'Africa AI startup Kenya Nigeria South Africa', 'Middle East AI startup UAE Saudi Arabia'][day % 4]
    native = {
        'cn': ('中国 AI 初创公司 新产品 种子轮', '中国 小众 AI 独立开发 开源 垂直行业 工具 新发布'),
        'jp': ('日本 AI スタートアップ 新サービス シード 資金調達', '日本 ニッチ AI 個人開発 業務特化 オープンソース 新製品'),
        'kr': ('한국 AI 스타트업 신규 서비스 시드 투자', '한국 소규모 AI 부트스트랩 오픈소스 산업 특화 출시'),
    }
    result = []
    for market in markets_for(region):
        label = emerging if market == 'other' else MARKETS[market][0]
        launch, long_tail = native.get(market, (
            f'{label} emerging AI startup seed new product launch',
            f'{label} lesser known AI bootstrapped indie open source vertical product launch'))
        if market == 'eu':
            long_tail += [' neue KI Werkzeuge Gründer', ' outils IA jeunes startups',
                          ' nuevas herramientas IA startups', ' Nordic Baltic AI startup'][day % 4]
        if market == 'sea':
            long_tail += [' startup AI Indonesia baru', ' công cụ AI Việt Nam ra mắt',
                          ' Thailand AI startup', ' Malaysia Philippines AI startup'][day % 4]
        # Both lanes run every day. Hardware-only/software-only also constrain news.
        type_hint = (' AI hardware robotics devices' if product_type == 'hardware'
                     else ' AI software tools' if product_type == 'software' else '')
        result.extend([
            {'region': market, 'lane': 'launch', 'topic': 'news', 'query': f'{launch}{type_hint} {now.year}'},
            {'region': market, 'lane': 'niche', 'topic': 'general', 'query': f'{long_tail} {niche} {now.year}'},
        ])
    return result


def balanced_articles(articles, limit, region='all'):
    """Round robin by market and lane, then by publisher within each lane.

    De-duplicate across lanes without letting a high-volume English feed take
    every slot before other markets have a chance to reach the model.
    """
    groups = defaultdict(lambda: defaultdict(deque))
    for article in articles:
        market = article.get('search_region') or FEED_MARKETS.get(article['source'], 'other')
        if market not in markets_for(region):
            continue
        lane = article.get('search_lane', 'rss')
        publisher = urlsplit(article['url']).hostname
        groups[(market, lane)][publisher].append(article)
    queues = {}
    for group, publishers in groups.items():
        queue = deque()
        while any(publishers.values()):
            for items in publishers.values():
                if items:
                    queue.append(items.popleft())
        queues[group] = queue
    selected, seen = [], set()
    order = [(market, lane) for lane in ('niche', 'launch', 'rss') for market in markets_for(region)]
    while len(selected) < limit:
        progress = False
        for group in order:
            items = queues.get(group, deque())
            while items and items[0]['url'] in seen:
                items.popleft()
            if items:
                article = items.popleft()
                selected.append(article)
                seen.add(article['url'])
                progress = True
                if len(selected) == limit:
                    break
        if not progress:
            break
    return selected


def company_market(country):
    code = str(country or '').strip().upper()
    return next((market for market, (_, codes) in MARKETS.items() if code in codes.split()), 'unknown')
