import random
from collections import OrderedDict
from pprint import pprint

import requests
from bs4 import BeautifulSoup

proxies = (
    '101.109.242.136:80',
    '202.169.238.51:53281',
    '212.90.167.90:65309'
)


def scrape_page(url):
    """
    """
    headers = {
        'Connection':'close',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:54.0) Gecko/20100101 Firefox/54.0'}
    proxy = random.choice(proxies)
    print('Proxy:', proxy)
    r = requests.get(url, proxies=dict(http=proxy), headers=headers)
    content = r.content.decode('utf-8')

    page = BeautifulSoup(content, 'html.parser')

    title = page.find('h1', {'id': 'title'})
    if title is None:
        if 'Robot Check' in content:
            print('Oh-oh, robot check failed. Shuffle proxy list and/or UA list...')
        else:
            print('The title is missing for "{}". Skipping :-('.format(url))
        open('content.txt', 'w').write(content)
        return
    book_name = ' - '.join(x.text.strip() for x in title.findAll('span'))

    result = dict(book_name=book_name,
                  categories=OrderedDict())

    categories = page.find_all('li', {'class': 'zg_hrsr_item'})
    for c in categories:
        name = '/'.join(x.text for x in c.find_all('a'))
        rank = int(c.find('span', {'class': 'zg_hrsr_rank'}).text[1:])
        result['categories'][name] = rank

    # Add the Amazon best seller rank as another category
    text = page.find('li', {'id': 'SalesRank'}).text
    tokens = [a for a in text.split('\n') if a]
    name = tokens[0].split(':')[0]
    rank = int(tokens[1].split()[0][1:].replace(',', ''))
    result['categories'][name] = rank

    return result


def main():
    book_urls = (
        'https://www.amazon.com/Mastering-Kubernetes-Gigi-Sayfan-ebook/dp/B01MXVUXDY',
        'https://www.amazon.com/Mastering-Kubernetes-Gigi-Sayfan/dp/1786461005'
    )

    for url in book_urls:
        r = scrape_page(url)
        pprint(r)
        print('-' * 10)


if __name__ == '__main__':
    main()
