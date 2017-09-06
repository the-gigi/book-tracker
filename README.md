# book-tracker

Keep track of the sales rank of books on Amazon

# Installation

`pip install -r requirements.txt`


# REST API + Admin interface

Launch with:

`sandman2ctl sqlite+pysqlite:///book-tracker.db`

a REST API is available at `http://localhost:5000`

The admin interface is avaialble at: `http://localhost:5000/admin`


# Query to find the floor of number of books sold based on total Amazon sales rank

`sqlite3 book-tracker.db "select count(*) from rank where category_id=6 and change < 0;"`

# Queries to find floor of number of books sold based on average change in categories


Ignore the global best seller rank, average the other categories and pick those with average less then -1

```select * from (select book_id, timestamp, avg(change) as average
   from rank where category_id <> 6 group by timestamp, book_id)
   where average < -1;```


```select * from (select book_id, timestamp, avg(change) as average from rank where category_id <> 6 group by timestamp, book_id) where average < -1;"


Use 2 sub-selects. first select all the negative changes. Then, group them by timestamp and book id. Finally, keep only
those times and books were all 4 categories (including the global AWS best seller rank) improved at the same time.

```select book_id, timestamp from (
        select book_id, timestamp, count(*) as changes from (
            select * from rank where change < 0)
        group by timestamp, book_id)
   where changes = 4;```


# Reference

http://scrapoxy.io/
https://superuser.com/questions/322376/how-to-install-the-real-firefox-on-debian
http://scraping.pro/use-headless-firefox-scraping-linux/ (old, using xvfb)
https://developer.mozilla.org/en-US/Firefox/Headless_mode (Node.js)
https://intoli.com/blog/running-selenium-with-headless-firefox/ (Python on Windows)
https://developers.google.com/web/updates/2017/04/headless-chrome