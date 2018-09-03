# book-tracker

Keep track of the sales rank of books on Amazon

# Installation


Requires [pipenv](https://docs.pipenv.org/)

`pipenv install`


# REST API + Admin interface

Launch with:

`sandman2ctl sqlite+pysqlite:///book-tracker.db`

a REST API is available at `http://localhost:5000`

The admin interface is avaialble at: `http://localhost:5000/admin`


# Queries

## Query to find the floor of number of books sold based on rank change of more than 12500 (applies to best seller rank)

```
select count(*) from rank where change < -12500;
```

Use with watch to monitor change

```
watch -n 360 'sqlite3 book-tracker.db "select count(*) from rank where change < -12500;"'
```

## Queries to find floor of number of books sold based on average change in categories

Ignore the global best seller rank, average the other categories and pick those with average less then -1

```select * from (select book_id, timestamp, avg(change) as average
   from rank where category_id <> 6 group by timestamp, book_id)
   where average < -1;```


```select * from (select book_id, timestamp, avg(change) as average from rank where category_id <> 6 group by timestamp, book_id) where average < -1;"


Use 2 sub-selects. first select all the negative changes. Then, group them by timestamp and book id. Finally, keep only
those times and books were all 4 categories (including the global AWS best seller rank) improved at the same time and
the sum of changes was less than 5000 to accomodate for eal shift and not just Amazon removing other books from
category.

```select book_id, timestamp from (
        select book_id, timestamp, count(*) as changes, sum(change) as total  from (
            select * from rank where change < 0)
        group by timestamp, book_id)
   where changes = 4 and total < -12500;```


```

## Here is the ultimate query, including time formatting
```
sqlite3 book-tracker.db "select book_id, strftime('%m-%d-%Y %H:%M', timestamp), rank, change from rank where timestamp in (select timestamp from rank where change < -12500) and category_id=6 and change < -12500 and timestamp > datetime('now','-2 day');"
```