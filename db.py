import os

from sqlalchemy import create_engine
from sqlalchemy.engine import base
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from models import Base

Session = None


def get_session():
    if Session is None:
        init()
    return Session()


def init():
    connection_string = os.environ['BOOK_TRACKER_CONNECTION_STRING']
    db = create_engine(connection_string)
    global Session
    Session = sessionmaker(db)
    Base.metadata.create_all(db)
