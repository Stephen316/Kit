import sqlite3
import sys
from pathlib import Path

from ClaimWire import CLAIM_NAME, read_frame, send_frame
from Ledger import Ledger
from RecoveryFence import StaleOwner, check_owner, owner_digest
from SingleClaim import claim_to_file


def handle(store, claims, sequence, request):
    if (
        set(request) != {"sequence", "owner", "worker", "pool", "name"}
        or type(request["sequence"]) is not int
        or request["sequence"] != sequence
        or not isinstance(request["name"], str)
        or not CLAIM_NAME.fullmatch(request["name"])
    ):
        raise ValueError("invalid claim helper request")
    owner_digest(request["owner"])
    with Ledger(store) as ledger:
        check_owner(ledger.db, request["owner"])
        result = claim_to_file(
            ledger, request["worker"], request["pool"], claims / request["name"]
        )
    return result


def run(store, claims, source, sink):
    if not claims.is_dir() or claims.is_symlink():
        raise ValueError("claim helper requires its private claim directory")
    sequence = 0
    while True:
        request = read_frame(source)
        if request is None:
            return
        sequence += 1
        try:
            result = handle(store, claims, sequence, request)
        except StaleOwner:
            send_frame(sink, {"sequence": sequence, "error": "stale_owner"})
            return
        except (
            OSError,
            ValueError,
            KeyError,
            TypeError,
            RecursionError,
            sqlite3.Error,
        ):
            send_frame(sink, {"sequence": sequence, "error": "claim_failed"})
            return
        send_frame(sink, {"sequence": sequence, "result": result})


if __name__ == "__main__":
    if sys.platform != "win32" or len(sys.argv) != 3:
        raise SystemExit("expected the Windows store and private claim directory")
    run(Path(sys.argv[1]), Path(sys.argv[2]), sys.stdin.buffer, sys.stdout.buffer)
