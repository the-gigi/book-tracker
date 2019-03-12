import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base

nop = lambda: None

CreateSession = nop


def get_session():
    if CreateSession == nop:
        init()
    return CreateSession()


def init():
    connection_string = os.environ.get('BOOK_TRACKER_CONNECTION_STRING', 'sqlite:///book-tracker.db')
    db = create_engine(connection_string)
    global CreateSession
    CreateSession = sessionmaker(db)
    Base.metadata.create_all(db)
