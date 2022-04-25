# Install book-tracker
pipenv install

# Populate DB
pipenv run python -c 'from db import init; init()'
sqlite3 book-tracker.db < book.sql

