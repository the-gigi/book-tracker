from datetime import datetime, timedelta
import time

from db import get_session
from scrape_page import scrape_page

import models as m


def fetch_book_urls():
    session = get_session()
    q = session.query
    urls = q(m.Book.url).all()
    return urls


def update_rank(category_name, rank):
    session = get_session()
    q = session.query

    categories = q(m.Category.name).all()
    if category_name not in categories:
        session.add(m.Category())

def track_books():
    try:
        books = fetch_book_urls()
        for book in books:
            r = scrape_page(book.url)
            for category_name, rank in r['categories'].items():
                update_rank(category_name, rank)
    except Exception as e:
        pass


def main():
    """

    """
    hour = timedelta(hours=1)
    while True:
        start = datetime.now()
        track_books()
        until_next_hour = (start + hour - datetime.now()).seconds
        time.sleep(until_next_hour)


if __name__ == '__main__':
    main()
