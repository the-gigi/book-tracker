# Kill hung book_tracker + Chromium processes
kill -9 $(ps aux | grep book_tracker | grep -v grep | awk '{ print $2 }')
killall Chromium
