from datetime import datetime, timedelta, timezone
import time

from .db import get_session
from .scrape_page import scrape_page
from . import models as m

HOUR = timedelta(hours=1)
MAX_RETRIES = 3


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None, second=0, microsecond=0)


def fmt(dt):
    """Format a naive UTC datetime as local time string."""
    return dt.replace(tzinfo=timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M')


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


def scrape_with_retries(url):
    for attempt in range(MAX_RETRIES):
        try:
            rank = scrape_page(url)
            if rank is not None:
                return rank
        except Exception as e:
            print(f'  Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}')
        if attempt < MAX_RETRIES - 1:
            backoff = 2 ** attempt * 5
            print(f'  Retrying in {backoff}s...')
            time.sleep(backoff)
    return None


def track_books():
    session = get_session()
    now = utcnow()
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
            print(f'Sleeping {until_next_hour // 60} minutes until {fmt(timestamp)}')
            time.sleep(until_next_hour)
        else:
            timestamp = now

        books = q(m.Book).filter_by(track=True).all()
        print(f'[{fmt(timestamp)}] --------------------')
        max_book_name = max(len(b.name) for b in books)
        category_name = 'Amazon Best Sellers Rank'
        for book in books:
            rank = scrape_with_retries(book.url)
            if rank is None:
                print(f'{book.name: <{max_book_name}} : FAILED (skipping)')
                continue

            print(f'{book.name: <{max_book_name}} : {rank:,}')
            update_rank(session, book, category_name, rank, timestamp)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f'Error: {e}')
    finally:
        naptime = (timestamp + HOUR - utcnow()).seconds
        time.sleep(naptime)


def main():
    """
    """
    while True:
        track_books()


if __name__ == '__main__':
    main()
