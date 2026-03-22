"""Initialize the local database and seed it from book.sql."""

from __future__ import annotations

import pathlib
import sqlite3

from .db import init


def main() -> None:
    init()
    db_path = pathlib.Path("book-tracker.db")
    sql_path = pathlib.Path("book.sql")
    if not sql_path.exists():
        raise FileNotFoundError("book.sql not found")

    with sqlite3.connect(db_path) as conn:
        conn.executescript(sql_path.read_text())
        conn.commit()


if __name__ == "__main__":
    main()
