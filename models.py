from datetime import datetime
from sqlalchemy import (Column,
                        DateTime,
                        ForeignKey,
                        Integer,
                        String,
                        Boolean,
                        Index)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()
metadata = Base.metadata


class Book(Base):
    __tablename__ = 'book'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), unique=True, nullable=False, index=True)
    isbn = Column(String(13), nullable=False)
    url = Column(String(1024), nullable=False)
    track = Column(Boolean, default=True, index=True)


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(1024))


class Rank(Base):
    __tablename__ = 'rank'
    id = Column(Integer, primary_key=True)
    book_id = Column(ForeignKey('book.id'), nullable=False)
    category_id = Column(ForeignKey('category.id'), nullable=False)
    rank = Column(Integer, nullable=False)
    change = Column(Integer)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)

    book = relationship('Book')
    category = relationship('Category')

    Index('ix_book_category_timestamp', 'book', 'category', 'timestamp', unique=True)