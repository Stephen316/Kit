"""Corpus coverage and limit measurements after the member-boundary pass.

Reads every unique BRep member listed in VerifyAll.json with the production
typed codec, re-emits it, and records the status. It also measures, with the
independent research scanner, the largest record token count, the largest
bulletin-board change list and the largest delta-state board list.
Usage: python3.14 -I VerifyBounds.py [--src DIR] [--out FILE] [--baseline FILE]
--src reads with another source tree, for example the base commit exported
with git archive. --baseline takes the rows of such a run as the before state.
"""

import argparse
import collections
import json
import sys
import time
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PARSER = argparse.ArgumentParser()
PARSER.add_argument("--src", default=str(ROOT / "src"))
PARSER.add_argument("--out", default=str(HERE / "VerifyBounds.json"))
PARSER.add_argument("--baseline")
ARGS = PARSER.parse_args()
sys.path.insert(0, ARGS.src)
sys.path.insert(0, str(HERE))

import AsmScan  # noqa: E402

from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry  # noqa: E402


def board_sizes(records):
    """Walk each delta_state record with its documented layout.

    Layout: id, two flags, five refs, a logical name flag with an optional
    text, then boards as presence 1, owner ref, status long and changes as
    presence 1 with two refs, each list closed by presence 0.
    """
    largest_changes = 0
    largest_boards = 0
    for record in records:
        if record["name"] != "delta_state":
            continue
        tokens = [tuple(token) for token in record["tokens"]]
        index = 8
        if tokens[index][0] == 10:
            index += 1
        index += 1
        boards = 0
        while tokens[index] == (4, 1):
            boards += 1
            index += 3
            changes = 0
            while tokens[index] == (4, 1):
                changes += 1
                index += 3
            if tokens[index] != (4, 0):
                raise ValueError("unexpected board change terminator")
            index += 1
            largest_changes = max(largest_changes, changes)
        if tokens[index] != (4, 0):
            raise ValueError("unexpected board list terminator")
        largest_boards = max(largest_boards, boards)
    return largest_changes, largest_boards


def main():
    previous = json.loads((HERE / "VerifyAll.json").read_text())["members"]
    before = {}
    if ARGS.baseline:
        for row in json.loads(Path(ARGS.baseline).read_text())["members"]:
            before[(row["path"], row["member"])] = row["status"] if row["status"] != "error" else row["error"]
    rows = []
    status = collections.Counter()
    failures = collections.Counter()
    largest = collections.Counter()
    where = {}
    start = time.time()
    for item in previous:
        with zipfile.ZipFile(ROOT / item["path"]) as archive:
            payload = archive.read(item["member"])
        _, _, records = AsmScan.records(payload)
        tokens = max(len(record["tokens"]) for record in records)
        changes, boards = board_sizes(records)
        for key, value in (("recordTokens", tokens), ("boardChanges", changes), ("stateBoards", boards)):
            if value > largest[key]:
                largest[key] = value
                where[key] = item["path"]
        entry = dict(path=item["path"], member=item["member"], sha256=item["sha256"], previous=before.get((item["path"], item["member"]), item["status"] if item["status"] == "exact" else item.get("error", item["status"])), recordTokens=tokens, boardChanges=changes, stateBoards=boards)
        try:
            if item["member"].endswith(".smbh"):
                same = EmitJournal(ReadJournal(payload)) == payload
            else:
                same = EmitGeometry(ReadGeometry(payload)) == payload
            entry["status"] = "exact" if same else "differs"
        except ValueError as error:
            entry["status"] = "error"
            entry["error"] = str(error)[:200]
            failures[str(error)[:120]] += 1
        status[entry["status"]] += 1
        rows.append(entry)
    transitions = collections.Counter((row["previous"][:80], row["status"] if row["status"] != "error" else row["error"][:80]) for row in rows if row["previous"] != "exact" or row["status"] != "exact")
    summary = dict(
        source="baseline run" if ARGS.baseline else "VerifyAll.json",
        before=dict(collections.Counter("exact" if row["previous"] == "exact" else "error" for row in rows)),
        members=len(rows),
        status=dict(status),
        failures=failures.most_common(),
        largest=dict(largest),
        largestAt=where,
        transitions=[dict(previous=key[0], now=key[1], count=count) for key, count in transitions.most_common()],
        seconds=round(time.time() - start, 1),
    )
    Path(ARGS.out).write_text(json.dumps(dict(summary=summary, members=rows), indent=1) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
