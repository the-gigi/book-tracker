# book-tracker

Keep track of the sales rank of books on Amazon

# Installation

`pip install -r requirements.txt`


# REST API + Admin interface

Launch with:

`sandman2ctl sqlite+pysqlite:///book-tracker.db`

a REST API is available at `http://localhost:5000`

The admin interface is avaialble at: `http://localhost:5000/admin`


# Query to find the floor of number of books sold

`sqlite3 book-tracker.db "select count(*) from rank where category_id=6 and change < 0;"`

