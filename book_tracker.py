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
    timestamp = datetime.utcnow().replace(second=0, microsecond=0)
    try:
        q = session.query
        last_update_time = q(m.Rank).order_by(m.Rank.timestamp.desc()).first().timestamp
        time_since_last_update = timestamp - last_update_time
        if time_since_last_update < HOUR:
            timestamp = last_update_time + HOUR
            until_next_hour = (last_update_time + HOUR - timestamp).seconds
            print(f'Sleeping {until_next_hour // 60} minutes until {last_update_time + HOUR}')
            time.sleep(until_next_hour)

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
