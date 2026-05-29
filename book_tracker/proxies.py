import json
import random
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import urlopen

# Refreshed 2026-05-28 from public proxy feeds and tested locally.
# Candidates were required to support HTTPS and reach amazon.com/robots.txt.
# Public proxies can still be challenged on Amazon product pages.
SEED_PROXIES = """
DIRECT
170.106.136.181:31002
192.99.8.15:8850
104.194.9.31:8888
189.232.80.234:8080
159.65.5.53:8080
176.111.37.5:39811
185.200.188.234:10001
185.234.66.87:1082
176.111.37.216:39811
200.174.198.32:8888
194.59.204.87:9080
152.67.191.232:6800
113.160.132.26:8080
190.212.131.238:3128
45.89.106.12:8080
176.222.54.139:8080
169.197.182.33:8080
185.191.239.248:3128
20.164.75.153:8080
""".split()

STATE_FILE = Path('proxy_state.json')
POOL_FILE = Path('proxy_pool.json')
LOG_FILE = Path('scrape.log')
REFRESH_INTERVAL = timedelta(hours=4)
POOL_VALIDATION_VERSION = 'amazon-product-v1'
MAX_CANDIDATES = 900
MAX_PROXIES_TO_TEST = 350
MAX_FRESH_PROXIES = 40
ROBOT_CHECK_QUARANTINE = timedelta(hours=24)
TIMEOUT_QUARANTINE = timedelta(hours=6)
RANK_MISSING_QUARANTINE = timedelta(hours=3)
GENERAL_QUARANTINE = timedelta(hours=2)
PROXY_SOURCES = (
    'https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/http/data.txt',
    'https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt',
    'https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/https/data.txt',
    'https://raw.githubusercontent.com/wiki/gfpcom/free-proxy-list/lists/http.txt',
    'https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=3000&country=all&ssl=all&anonymity=all',
)
PROXY_RE = re.compile(r'(?:https?://)?((?:\d{1,3}\.){3}\d{1,3}:\d{2,5})')
PRODUCT_TEST_URLS = (
    'https://www.amazon.com/Design-Multi-Agent-Systems-Using-MCP/dp/1806116472',
    'https://www.amazon.com/Design-Multi-Agent-Systems-Using-MCP-ebook/dp/B0G7YKPBCW/',
)
TEST_USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'
)


def utcnow():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.isoformat()


def parse_time(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def log_proxy(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with LOG_FILE.open('a') as f:
        f.write(f'[{timestamp}] proxy_refresh {message}\n')


def load_state():
    try:
        with STATE_FILE.open() as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def save_state(state):
    with STATE_FILE.open('w') as f:
        json.dump(state, f, indent=2, sort_keys=True)


def mark_validated_proxies(proxies):
    state = load_state()
    now = iso(utcnow())
    for proxy in proxies:
        record = state.setdefault(proxy, {})
        record.setdefault('successes', 0)
        record.setdefault('failures', 0)
        record['consecutive_failures'] = 0
        record['last_success'] = now
        record['last_reason'] = None
        record['quarantine_until'] = None
    save_state(state)


def load_pool():
    try:
        with POOL_FILE.open() as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    proxies = data.get('proxies')
    if not isinstance(proxies, list):
        return None
    return data


def save_pool(proxy_list):
    data = {
        'refreshed_at': iso(utcnow()),
        'validation': POOL_VALIDATION_VERSION,
        'proxies': proxy_list,
    }
    with POOL_FILE.open('w') as f:
        json.dump(data, f, indent=2, sort_keys=True)


def pool_is_fresh(pool):
    refreshed_at = parse_time(pool.get('refreshed_at'))
    return (
        pool.get('validation') == POOL_VALIDATION_VERSION
        and refreshed_at is not None
        and refreshed_at + REFRESH_INTERVAL > utcnow()
    )


def fetch_proxy_source(url):
    try:
        with urlopen(url, timeout=12) as response:
            return response.read().decode('utf-8', 'ignore')
    except Exception as e:
        log_proxy(f'event=source_failed url={url} error={type(e).__name__}: {e}')
        return ''


def fetch_proxy_candidates():
    candidates = []
    seen = set()
    for source in PROXY_SOURCES:
        text = fetch_proxy_source(source)
        for match in PROXY_RE.finditer(text):
            proxy = match.group(1)
            if proxy in seen:
                continue
            seen.add(proxy)
            candidates.append(proxy)
            if len(candidates) >= MAX_CANDIDATES:
                return candidates
    return candidates


def test_proxy(proxy):
    start = time.monotonic()
    test_url = random.choice(PRODUCT_TEST_URLS)
    cmd = [
        'curl',
        '-fsSL',
        '--proxy',
        f'http://{proxy}',
        '--connect-timeout',
        '4',
        '--max-time',
        '10',
        '--compressed',
        '-A',
        TEST_USER_AGENT,
        '-H',
        'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        '-H',
        'Accept-Language: en-US,en;q=0.9',
        '-w',
        '\nCURL_STATUS:%{http_code}',
        test_url,
    ]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=8,
        )
    except subprocess.TimeoutExpired:
        return None

    body = result.stdout or b''
    status = None
    if b'CURL_STATUS:' in body:
        body, status_bytes = body.rsplit(b'CURL_STATUS:', 1)
        try:
            status = int(status_bytes.strip()[:3])
        except ValueError:
            status = None

    body_lower = body.lower()
    blocked = any(
        marker in body
        for marker in (
            b'/errors/validateCaptcha',
            b'Robot Check',
            b'validateCaptcha',
            b'Click the button below to continue shopping',
        )
    )
    product_page = any(
        marker in body
        for marker in (
            b'id="productTitle"',
            b'id="title"',
            b'Best Sellers Rank',
            b'detailBulletsWrapper_feature_div',
        )
    ) or b'design multi-agent' in body_lower
    if status == 200 and product_page and not blocked:
        return proxy, time.monotonic() - start
    return None


def test_proxy_candidates(candidates):
    tested = candidates[:MAX_PROXIES_TO_TEST]
    good = []
    with ThreadPoolExecutor(max_workers=60) as executor:
        futures = [executor.submit(test_proxy, proxy) for proxy in tested]
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                good.append(result)

    good.sort(key=lambda item: item[1])
    return [proxy for proxy, _elapsed in good[:MAX_FRESH_PROXIES]]


def refresh_proxy_pool(force=False):
    pool = load_pool()
    if not force and pool is not None and pool_is_fresh(pool):
        return pool['proxies']

    candidates = fetch_proxy_candidates()
    fresh = test_proxy_candidates(candidates)
    if fresh:
        mark_validated_proxies(fresh)
        proxy_list = ['DIRECT'] + fresh
        save_pool(proxy_list)
        log_proxy(
            f'event=refreshed candidates={len(candidates)} '
            f'tested={min(len(candidates), MAX_PROXIES_TO_TEST)} good={len(fresh)}'
        )
        return proxy_list

    if (
        pool is not None
        and pool.get('validation') == POOL_VALIDATION_VERSION
        and pool.get('proxies')
    ):
        log_proxy(
            f'event=refresh_empty candidates={len(candidates)} '
            f'using_cached={len(pool["proxies"])}'
        )
        return pool['proxies']

    log_proxy(f'event=refresh_empty candidates={len(candidates)} using_seed=1')
    return SEED_PROXIES


def get_proxy_pool():
    return refresh_proxy_pool()


def get_proxy_state(state, proxy):
    return state.setdefault(
        proxy,
        {
            'successes': 0,
            'failures': 0,
            'consecutive_failures': 0,
            'last_success': None,
            'last_failure': None,
            'last_reason': None,
            'quarantine_until': None,
        },
    )


def is_quarantined(record, now):
    quarantine_until = parse_time(record.get('quarantine_until'))
    return quarantine_until is not None and quarantine_until > now


def proxy_weight(proxy, state, now):
    record = state.get(proxy, {})
    if is_quarantined(record, now):
        return 0

    successes = int(record.get('successes') or 0)
    consecutive_failures = int(record.get('consecutive_failures') or 0)
    return max(1, 5 + successes - (2 * consecutive_failures))


def get_proxy(exclude=None):
    state = load_state()
    now = utcnow()
    exclude = set(exclude or ())
    proxy_pool = get_proxy_pool()
    choices = []
    for proxy in proxy_pool:
        if proxy in exclude:
            continue
        choices.extend([proxy] * proxy_weight(proxy, state, now))
    if not choices:
        log_proxy('event=pool_exhausted action=force_refresh')
        proxy_pool = refresh_proxy_pool(force=True)
        for proxy in proxy_pool:
            if proxy in exclude:
                continue
            choices.extend([proxy] * proxy_weight(proxy, state, now))

    if not choices:
        # All remaining proxies are quarantined. Fall back only to DIRECT if it
        # has not already been tried for this scrape, instead of recycling
        # endpoints known to be bad.
        choices = [] if 'DIRECT' in exclude else ['DIRECT']
    if not choices and len(exclude) >= len(proxy_pool):
        for proxy in proxy_pool:
            if proxy == 'DIRECT':
                continue
            choices.extend([proxy] * proxy_weight(proxy, state, now))
    if not choices:
        return None
    return random.choice(choices)


def quarantine_duration(reason, consecutive_failures):
    reason = reason or ''
    if 'robot check' in reason:
        return ROBOT_CHECK_QUARANTINE
    if 'TimeoutError' in reason or 'ERR_TIMED_OUT' in reason or 'timeout' in reason:
        return TIMEOUT_QUARANTINE
    if 'sales rank missing' in reason or 'rank not found' in reason:
        if consecutive_failures >= 2:
            return RANK_MISSING_QUARANTINE
        return None
    if consecutive_failures >= 3:
        return GENERAL_QUARANTINE
    return None


def record_proxy_success(proxy):
    if not proxy:
        return
    state = load_state()
    record = get_proxy_state(state, proxy)
    record['successes'] = int(record.get('successes') or 0) + 1
    record['consecutive_failures'] = 0
    record['last_success'] = iso(utcnow())
    record['last_reason'] = None
    record['quarantine_until'] = None
    save_state(state)


def record_proxy_failure(proxy, reason):
    if not proxy:
        return
    state = load_state()
    record = get_proxy_state(state, proxy)
    record['failures'] = int(record.get('failures') or 0) + 1
    record['consecutive_failures'] = int(record.get('consecutive_failures') or 0) + 1
    record['last_failure'] = iso(utcnow())
    record['last_reason'] = reason

    duration = quarantine_duration(reason, record['consecutive_failures'])
    if duration is not None:
        record['quarantine_until'] = iso(utcnow() + duration)

    save_state(state)
