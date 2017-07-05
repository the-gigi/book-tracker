from datetime import datetime
from sqlalchemy import (Column,
                        DateTime,
                        ForeignKey,
                        Integer,
                        String,
                        Boolean)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()
metadata = Base.metadata


class Book(Base):
    __tablename__ = 'book'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), unique=True, nullable=False)
    isbn = Column(String(13), nullable=False)
    url = Column(String(1024), nullable=False)
    track = Column(Boolean, default=True)


class Categories(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = url = Column(String(1024))


class SalesRank(Base):
    id = Column(Integer, primary_key=True)
    book_id = Column(ForeignKey('book.id'), nullable=False)
    category_id = Column(ForeignKey('category.id'), nullable=False)
    rank = Column(Integer, nullable=False)

    book = relationship('Book')
    category = relationship('Category')

