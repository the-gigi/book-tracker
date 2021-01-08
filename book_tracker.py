import traceback

from datetime import datetime, timedelta
import time

from db import get_session
from scrape_page import scrape_page
import models as m

HOUR = timedelta(hours=1)


def update_rank(session, book, category_name, rank, timestamp):
    q = session.query
    category = q(m.Category).filter_by(name=category_name).scalar()
    if category is None:
        category = m.Category(name=category_name)
        session.add(category)
    try:
        last_rank = q(m.Rank).filter_by(book=book, category=category).order_by(m.Rank.timestamp.desc()).first().rank
        change = rank - last_rank
    except Exception as e:
        change = 0

    rank = m.Rank(book=book,
                  category=category,
                  rank=rank,
                  change=change,
                  timestamp=timestamp)
    session.add(rank)


def track_books():
    session = get_session()
    now = datetime.utcnow().replace(second=0, microsecond=0)
    timestamp = now
    try:
        q = session.query
        try:
            last_update_time = q(m.Rank).order_by(m.Rank.timestamp.desc()).first().timestamp
        except Exception as e:
            last_update_time = now - 2 * HOUR
        time_since_last_update = now - last_update_time
        if time_since_last_update < HOUR:
            timestamp = last_update_time + HOUR
            until_next_hour = (timestamp - now).seconds
            print(f'Sleeping {until_next_hour // 60} minutes until {timestamp}')
            time.sleep(until_next_hour)
        else:
            timestamp = now

        books = q(m.Book).filter_by(track=True).all()
        print(f'[{timestamp}] --------------------')
        max_book_name = max(len(b.name) for b in books)
        for book in books:
            rank = scrape_page(book.url)
            if rank is None:
                raise RuntimeError('Unable to scrape page')

            category_name = 'Amazon Best Sellers Rank'
            print(f'{book.name: <{max_book_name}} : {rank:,}')
            update_rank(session, book, category_name, rank, timestamp)
        session.commit()
    except Exception as e:
        session.rollback()
        traceback.print_exc()
    finally:
        naptime = (timestamp + HOUR - datetime.utcnow().replace(second=0, microsecond=0)).seconds
        time.sleep(naptime)


def main():
    """
    """
    while True:
        track_books()


if __name__ == '__main__':
    main()
