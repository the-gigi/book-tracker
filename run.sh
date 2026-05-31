#! /usr/bin/env zsh

pid_file=.book-tracker-watchdog.pid
surface=${BOOK_TRACKER_CMUX_SURFACE:-surface:41}

if [[ -f "$pid_file" ]]; then
    watchdog_pid=$(<"$pid_file")
    if ! kill -0 "$watchdog_pid" 2>/dev/null; then
        rm -f "$pid_file"
    fi
fi

if [[ ! -f "$pid_file" ]]; then
    uv run book-tracker-watchdog --surface "$surface" >> watchdog-process.log 2>&1 &
    echo $! > "$pid_file"
fi

uv run book-tracker
