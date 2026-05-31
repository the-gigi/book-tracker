#! /usr/bin/env zsh

surface=${BOOK_TRACKER_CMUX_SURFACE:-surface:41}

uv run book-tracker-watchdog --surface "$surface"
