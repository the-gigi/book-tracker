from datetime import datetime, timedelta
import time

from db import get_session
from scrape_page import scrape_page

import models as m


def fetch_books(session):

    return


def update_rank(session, book, category_name, rank, timestamp):
    q = session.query
    category = q(m.Category).filter_by(name=category_name).scalar()
    if category is None:
        category = m.Category(name=category_name)
        session.add(category)

    rank = m.Rank(book=book,
                  category=category,
                  rank=rank,
                  timestamp=timestamp)
    session.add(rank)


def track_books(timestamp):
    session = get_session()
    try:
        q = session.query
        books = q(m.Book).filter_by(track=True).all()
        for book in books:
            print(f'[{timestamp}] --- {book.name} ---')
            r = scrape_page(book.url)
            for category_name, rank in r['categories'].items():
                print(f'{category_name}: {rank}')
                update_rank(session, book, category_name, rank, timestamp)
        session.commit()
    except Exception as e:
        session.rollback()
        print(e)


def main():
    """
    """
    hour = timedelta(hours=1)
    while True:
        start = datetime.utcnow().replace(second=0, microsecond=0)
        track_books(start)
        until_next_hour = (start + hour - datetime.utcnow()).seconds
        time.sleep(until_next_hour)


if __name__ == '__main__':
    main()
