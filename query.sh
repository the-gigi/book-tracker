days=$1
if [[ $days == "" ]]; then
  days=2
fi

min_change=12000
sqlite3 book-tracker.db "select book_id, strftime('%m-%d-%Y %H:%M', timestamp), rank, change from rank where timestamp in (select timestamp from rank where change < -${min_change}) and category_id=(select id from category where name='Amazon Best Sellers Rank') and change < -${min_change} and timestamp > datetime('now','-${days} day');"
