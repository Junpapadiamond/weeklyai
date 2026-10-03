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
    use_hardware = product_type == 'hardware' or (product_type == 'mixed' and day % 5 < 2)
    niche = hardware if use_hardware else software
    # These are search targets, never inferred company nationality.
    emerging = ['India', 'Latin America Brasil México',
                'Africa Kenya Nigeria South Africa', 'Middle East UAE Saudi Arabia'][day % 4]
    native = {
        'cn': ('中国 AI 初创 新产品', '中国 小众 AI 工具 发布'),
        'jp': ('日本 AI スタートアップ 新サービス', '日本 ニッチ AI 新製品'),
        'kr': ('한국 AI 스타트업 신규 서비스', '한국 소규모 AI 서비스 출시'),
    }
    result = []
    for market in markets_for(region):
        label = emerging if market == 'other' else 'Southeast Asia' if market == 'sea' else MARKETS[market][0]
        launch, long_tail = native.get(market, (
            f'{label} AI startup product launch seed',
            f'{label} AI {niche.split("AI")[-1].strip()} launch'))
        if market in native:
            long_tail += {'cn': ' 智能硬件' if use_hardware else [' 独立开发', ' 开源', ' 垂直行业'][day % 3],
                          'jp': ' ロボット' if use_hardware else [' 個人開発', ' オープンソース', ' 業務特化'][day % 3],
                          'kr': ' 로봇' if use_hardware else [' 오픈소스', ' 부트스트랩', ' 산업특화'][day % 3]}[market]
        if market == 'eu':
            long_tail = ['Deutschland neue KI Werkzeuge Startup', 'France nouveaux outils IA startup',
                         'España nuevas herramientas IA startup', 'Nordic Baltic indie AI product launch'][day % 4]
            if use_hardware:
                long_tail += ' robotics hardware'
        if market == 'sea':
            long_tail = ['Indonesia startup AI baru', 'Việt Nam công cụ AI ra mắt',
                         'Thailand niche AI startup launch', 'Malaysia Philippines indie AI launch'][day % 4]
            if use_hardware:
                long_tail += ' robotics hardware'
        # Both lanes run every day. Hardware-only/software-only also constrain news.
        type_hint = (' AI hardware robotics devices' if product_type == 'hardware'
                     else ' AI software tools' if product_type == 'software' else '')
        result.extend([
            {'region': market, 'lane': 'launch', 'topic': 'news', 'query': f'{launch}{type_hint} {now.year}'},
            {'region': market, 'lane': 'niche', 'topic': 'general', 'query': f'{long_tail} {now.year}'},
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
