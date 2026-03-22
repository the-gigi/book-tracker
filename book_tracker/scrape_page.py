import random
from pprint import pprint

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

from .config import user_agents
from .proxies import get_proxy


def get_user_agent():
    return random.choice(user_agents)


def get_page_content(url):
    """Fetch page content using Playwright with a headless Chromium browser."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox'],
        )
        context = browser.new_context(
            user_agent=get_user_agent(),
        )
        page = context.new_page()
        try:
            page.goto(url, timeout=30000, wait_until='domcontentloaded')
            page.wait_for_timeout(3000)
            content = page.content()
        finally:
            browser.close()

    return content


def scrape_page(url):
    """Scrape the Amazon best sellers rank from a book page."""
    content = get_page_content(url)
    soup = BeautifulSoup(content, 'html.parser')

    title = soup.find('h1', {'id': 'title'}) or soup.find(id='productTitle')
    if title is None:
        if 'Robot Check' in content:
            print('Oh-oh, robot check failed. Shuffle proxy list and/or UA list...')
        else:
            print(f'The title is missing for "{url}". Skipping :-(')
        with open('content.txt', 'w') as f:
            f.write(content)
        return None

    # Try multiple patterns for finding the best sellers rank
    # Pattern 1: look for "Best Sellers Rank" in product details table
    for th in soup.find_all('th'):
        if 'Best Sellers Rank' in th.text:
            td = th.find_next_sibling('td')
            if td:
                rank_text = td.get_text()
                rank_str = rank_text.strip().split()[0].lstrip('#').replace(',', '')
                return int(rank_str)

    # Pattern 2: look for "Best Sellers Rank" in a span
    for span in soup.find_all('span'):
        text = span.get_text()
        if 'Best Sellers Rank' in text or 'Best-sellers rank' in text:
            # Extract rank number - usually follows "#"
            parts = text.split('#')
            if len(parts) > 1:
                rank_str = parts[1].strip().split()[0].replace(',', '')
                return int(rank_str)

    # Pattern 3: look in li#SalesRank (older Amazon layout)
    sales_rank_li = soup.find('li', {'id': 'SalesRank'})
    if sales_rank_li:
        text = sales_rank_li.get_text()
        parts = text.split('#')
        if len(parts) > 1:
            rank_str = parts[1].strip().split()[0].replace(',', '')
            return int(rank_str)

    print(f'Could not find sales rank for "{url}"')
    with open('content.txt', 'w') as f:
        f.write(content)
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
