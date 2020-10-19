days=$1
if [[ $days == "" ]]; then
  days=2
fi

# minimum change in rank to consider (default to 10,000 if environment variable is not defined)
min_change="${BOOK_TRACKER_MIN_CHANGE-10000}"

sqlite3 book-tracker.db "select strftime('%m-%d-%Y %H:%M', timestamp), book_id, rank, change from rank where timestamp in (select timestamp from rank where change < -${min_change}) and category_id=(select id from category where name='Amazon Best Sellers Rank') and change < -${min_change} and timestamp > datetime('now','-${days} day');"
