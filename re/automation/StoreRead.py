import sqlite3
from contextlib import closing, contextmanager

from RecoveryFence import check_owner


@contextmanager
def read_store(database, owner, versions, *, timeout=30):
    with closing(
        sqlite3.connect(
            database.as_uri() + "?mode=ro", uri=True, timeout=timeout, isolation_level=None
        )
    ) as db:
        db.row_factory = sqlite3.Row
        db.execute("BEGIN")
        if db.execute("PRAGMA user_version").fetchone()[0] not in versions:
            raise ValueError("unsupported research store version")
        check_owner(db, owner)
        yield db
