import sqlite3
from pathlib import Path
from typing import Any


class Sqlite:
    db_path: Path | None
    con: sqlite3.Connection
    cur: sqlite3.Cursor

    def __init__(self, db_path: Path | None = None) -> None:
        if db_path:
            self.con = sqlite3.connect(db_path)
        else:
            self.con = sqlite3.connect(":memory:")

        self.cur = self.con.cursor()

    def execute(
        self, query: str, params: tuple[Any, ...] | list[tuple[Any, ...]] | None = None
    ):
        if Path(query).exists():
            with Path(query).open("r") as f:
                query_string = f.read()
        else:
            query_string = query

        if params:
            if len(params) > 1:
                res = self.cur.executemany(query_string, params)
            else:
                res = self.cur.execute(query_string, params)
        else:
            res = self.cur.execute(query_string)

        if query_string.lower().startswith("insert"):
            self.con.commit()

        return res
