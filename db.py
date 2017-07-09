import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base

Session = None


def get_session():
    if Session is None:
        init()
    return Session()


def init():
    connection_string = os.environ.get('BOOK_TRACKER_CONNECTION_STRING', 'sqlite:///book-tracker.db')
    db = create_engine(connection_string)
    global Session
    Session = sessionmaker(db)
    Base.metadata.create_all(db)
