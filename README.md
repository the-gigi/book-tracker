# book-tracker

Keep track of the sales rank of books on Amazon

# Installation

## Install pre-requisites

Requires [sqlite3](https://www.sqlite.org) (already installed on Mac)
Requires [pipenv](https://docs.pipenv.org/)

## Run installation script
`$ ./install.sh`

# Command-line usage

`$ pipenv run python book_tracker.py`


## Killing it

Sometimes book tracker can get stuck due to networking issues, Run `kill.sh` to kill it and orphan Chromium instances too

# REST API + Admin interface
 
Launch with:

`$ pipenv run sandman2ctl sqlite+pysqlite:///book-tracker.db`

a REST API is available at `http://localhost:5000`

The admin interface is avaialble at: `http://localhost:5000/admin`


# Queries

The following query finds the floor of number of books sold based on rank change of more than 12500 (applies to best seller rank) grouped by book id.

```
sqlite3 book-tracker.db "select book_id,count(*) from rank where change < -12500 group by book_id order by book_id ;"
```

Use with watch to monitor change

```
watch -n 360 'sqlite3 book-tracker.db "select book_id,count(*) from rank where change < -12500 group by book_id order by book_id ;"'
```

The following queries find the floor of number of books sold based on average change in categories

Ignore the global best seller rank, average the other categories and pick those with average less then -1

```select * from (select book_id, timestamp, avg(change) as average
   from rank where category_id <> 6 group by timestamp, book_id)
   where average < -1;
```

```
select * from (select book_id, timestamp, avg(change) as average 
from rank where category_id <> 6 group by timestamp, book_id) where average < -1;"
```

Use 2 sub-selects. first select all the negative changes. Then, group them by timestamp and book id. Finally, keep only
those times and books where all 4 categories (including the global AWS best seller rank) improved at the same time and
the sum of changes was less than 12500 to accommodate for real shift and not just Amazon removing other books from
category.

```
select book_id, timestamp from (
    select book_id, timestamp, count(*) as changes, sum(change) as total  from (
        select * from rank where change < 0)
    group by timestamp, book_id)
where changes = 4 and total < -12500;```
```

```
select book_id, timestamp from (select book_id, timestamp, count(*) as changes, sum(change) as total  from (select * from rank where change < 0) group by timestamp, book_id) where changes = 4 and total < -12500;
```


## Here is the ultimate query, including time formatting
```bash
sqlite3 book-tracker.db "select book_id, strftime('%m-%d-%Y %H:%M', timestamp), rank, change from rank where timestamp in (select timestamp from rank where change < -30000) and category_id=(select id from category where name='Amazon Best Sellers Rank') and change < -30000 and timestamp > datetime('now','-2 day');"
```

If you want to watch for overall changes every hour:

```bash
watch -n 3600 -x sqlite3 book-tracker.db "select count(*) from rank where change < -30000;"
```
