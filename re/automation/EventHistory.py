import sqlite3
from contextlib import closing
from pathlib import Path

from Records import bounded
from RecoveryFence import check_owner

MAX_EVENT_ID = (1 << 63) - 1
PAGE_SIZE = 100


def event_window(root, owner, after, through):
    after = bounded(0 if after is None else after, 0, MAX_EVENT_ID)
    if through is not None:
        through = bounded(through, after, MAX_EVENT_ID)
    database = Path(root).resolve() / "ledger.sqlite3"
    if database.is_symlink() or not database.is_file():
        raise ValueError("event history requires an initialized store database")
    with closing(
        sqlite3.connect(
            database.as_uri() + "?mode=ro", uri=True, timeout=30, isolation_level=None
        )
    ) as db:
        db.row_factory = sqlite3.Row
        db.execute("BEGIN")
        if db.execute("PRAGMA user_version").fetchone()[0] not in (1, 2, 3, 4):
            raise ValueError("unsupported research store version")
        check_owner(db, owner)
        latest = db.execute("SELECT COALESCE(MAX(id), 0) FROM events").fetchone()[0]
        through = latest if through is None else through
        if not after <= through <= latest:
            raise ValueError("event bounds do not match this store's history")
        if (
            through
            and db.execute("SELECT 1 FROM events WHERE id=?", (through,)).fetchone()
            is None
        ):
            raise ValueError("event window end is not in this store's history")
        rows = db.execute(
            "SELECT id,at,job_id,action,detail FROM events WHERE id>? AND id<=? ORDER BY id LIMIT ?",
            (after, through, PAGE_SIZE + 1),
        ).fetchall()
    return {
        "events": [dict(row) for row in rows[:PAGE_SIZE]],
        "after": after,
        "through": through,
        "next_after": rows[PAGE_SIZE - 1]["id"] if len(rows) > PAGE_SIZE else None,
    }
