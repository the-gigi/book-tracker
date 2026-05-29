import random
import re
from datetime import datetime
from pprint import pprint

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

from .config import user_agents
from .proxies import get_proxy

LOG_FILE = 'scrape.log'
PAGE_TIMEOUT_MS = 15000
PAGE_SETTLE_MS = 2000
last_failure_reason = None


def get_user_agent():
    return random.choice(user_agents)


def get_proxy_config(proxy):
    if not proxy or proxy == 'DIRECT':
        return None
    server = proxy if '://' in proxy else f'http://{proxy}'
    return {'server': server}


def summarize_user_agent(user_agent):
    if ' Edg/' in user_agent:
        browser = 'Edge'
    elif ' Chrome/' in user_agent:
        browser = 'Chrome'
    elif ' Firefox/' in user_agent:
        browser = 'Firefox'
    elif ' Safari/' in user_agent:
        browser = 'Safari'
    else:
        browser = 'unknown'

    if 'Macintosh' in user_agent:
        platform = 'macOS'
    elif 'Windows' in user_agent:
        platform = 'Windows'
    elif 'Linux' in user_agent:
        platform = 'Linux'
    else:
        platform = 'unknown'

    return f'{browser}/{platform}'


def first_error_line(error):
    return str(error).splitlines()[0]


def log_fetch(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f'[{timestamp}] {message}\n')


def set_failure_reason(reason):
    global last_failure_reason
    last_failure_reason = reason


def get_last_failure_reason():
    return last_failure_reason or 'unknown'


def get_page_content(url, attempt=None, proxy=None):
    """Fetch page content using Playwright with a headless Chromium browser."""
    user_agent = get_user_agent()
    if proxy is None:
        proxy = get_proxy()
    proxy_config = get_proxy_config(proxy)
    attempt_label = f'attempt={attempt}' if attempt is not None else 'attempt=n/a'
    log_fetch(
        f'{attempt_label} event=fetch proxy={proxy or "direct"} '
        f'ua={summarize_user_agent(user_agent)} url={url}'
    )
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
            ],
            proxy=proxy_config,
        )
        context = browser.new_context(
            user_agent=user_agent,
            locale='en-US',
            timezone_id='America/Los_Angeles',
            viewport={'width': 1365, 'height': 900},
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
            },
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = context.new_page()
        page.set_default_timeout(PAGE_TIMEOUT_MS)
        page.set_default_navigation_timeout(PAGE_TIMEOUT_MS)
        try:
            response = page.goto(
                url,
                timeout=PAGE_TIMEOUT_MS,
                wait_until='domcontentloaded',
            )
            page.wait_for_timeout(PAGE_SETTLE_MS)
            content = page.content()
            status = response.status if response is not None else 'n/a'
            log_fetch(
                f'{attempt_label} event=result status={status} '
                f'blocked={is_blocked(content)} final_url={page.url}'
            )
        except Exception as e:
            log_fetch(
                f'{attempt_label} event=result status=n/a '
                f'error={type(e).__name__}: {first_error_line(e)} '
                f'final_url={page.url}'
            )
            raise
        finally:
            browser.close()

    return content


def write_debug_content(content):
    with open('content.txt', 'w') as f:
        f.write(content)


def is_blocked(content):
    return any(
        marker in content
        for marker in (
            '/errors/validateCaptcha',
            'Robot Check',
            'Click the button below to continue shopping',
            'validateCaptcha',
        )
    )


def normalize_text(soup):
    return re.sub(r'\s+', ' ', soup.get_text(' ', strip=True))


def extract_rank_from_text(text):
    patterns = (
        r'Best Sellers Rank\s*:?\s*#\s*([\d,]+)\s+in\s+Books\b',
        r'Best Sellers Rank\s*:?\s*#\s*([\d,]+)\b',
        r'Best-sellers rank\s*:?\s*#\s*([\d,]+)\b',
        r'Sales Rank\s*:?\s*#\s*([\d,]+)\b',
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1).replace(',', ''))
    return None


def extract_first_hash_rank(text):
    match = re.search(r'#\s*([\d,]+)\b', text)
    if match:
        return int(match.group(1).replace(',', ''))
    return None


def extract_rank(soup):
    # Newer Amazon book pages expose rank in detail bullets rather than in a
    # product details table.
    detail_bullets = soup.find(id='detailBulletsWrapper_feature_div')
    if detail_bullets:
        rank = extract_rank_from_text(normalize_text(detail_bullets))
        if rank is not None:
            return rank

    product_details = soup.find(id='prodDetails')
    if product_details:
        rank = extract_rank_from_text(normalize_text(product_details))
        if rank is not None:
            return rank

    # Older Amazon layout: product details table.
    for th in soup.find_all('th'):
        if 'Best Sellers Rank' in th.get_text(' ', strip=True):
            td = th.find_next_sibling('td')
            if td:
                rank = extract_first_hash_rank(normalize_text(td))
                if rank is not None:
                    return rank

    sales_rank_li = soup.find('li', {'id': 'SalesRank'})
    if sales_rank_li:
        rank = extract_rank_from_text(normalize_text(sales_rank_li))
        if rank is not None:
            return rank

    return extract_rank_from_text(normalize_text(soup))


def scrape_page(url, attempt=None, proxy=None):
    """Scrape the Amazon best sellers rank from a book page."""
    set_failure_reason(None)
    content = get_page_content(url, attempt=attempt, proxy=proxy)
    soup = BeautifulSoup(content, 'html.parser')

    if is_blocked(content):
        set_failure_reason('robot check')
        log_fetch(f'attempt={attempt} event=failed reason="robot check" url={url}')
        write_debug_content(content)
        return None

    rank = extract_rank(soup)
    if rank is not None:
        return rank

    title = soup.find('h1', {'id': 'title'}) or soup.find(id='productTitle')
    if title is None:
        set_failure_reason('sales rank missing')
        log_fetch(
            f'attempt={attempt} event=failed reason="sales rank missing" url={url}'
        )
        write_debug_content(content)
        return None

    set_failure_reason('rank not found')
    log_fetch(f'attempt={attempt} event=failed reason="rank not found" url={url}')
    write_debug_content(content)
    return None


def main():
    book_urls = (
        'https://www.amazon.com/Mastering-Kubernetes-container-orchestration-distributed-ebook-dp-B08BLLY5B8/dp/B08BLLY5B8',
        # 'https://www.amazon.com/Mastering-Kubernetes-Gigi-Sayfan-ebook/dp/B01MXVUXDY',
        # 'https://www.amazon.com/Mastering-Kubernetes-Gigi-Sayfan/dp/1786461005'
    )

    for url in book_urls:
        r = scrape_page(url)
        pprint(r)
        print('-' * 10)


if __name__ == '__main__':
    main()
