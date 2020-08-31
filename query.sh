days=$1
if [[ $days == "" ]]; then
  days=2
fi

sqlite3 book-tracker.db "select book_id, strftime('%m-%d-%Y %H:%M', timestamp), rank, change from rank where timestamp in (select timestamp from rank where change < -30000) and category_id=(select id from category where name='Amazon Best Sellers Rank') and change < -10000 and timestamp > datetime('now','-${days} day');"
