import json
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(BASE))

import AsmScan  # noqa: E402

TAGN = {4: "i", 6: "d", 7: "s", 10: "T", 11: "F", 12: "@", 13: "N", 14: "P", 15: "{", 16: "}", 19: "pos", 20: "vec", 21: "e", 23: "w"}


def fmt(tag, value):
    if tag in (10, 11, 15, 16):
        return TAGN[tag]
    if tag in (19, 20):
        return TAGN[tag] + "(" + ",".join(f"{v:.6g}" for v in value) + ")"
    if tag == 6:
        return f"{value:.10g}"
    if tag in (13, 14):
        return f"<{value}>"
    if tag == 7:
        return json.dumps(value)
    return f"{TAGN.get(tag, tag)}{value}"


def load(rel, member_suffix=None):
    with zipfile.ZipFile(ROOT / rel) as archive:
        for member in archive.namelist():
            if member.endswith((".smb", ".smbh")) and (member_suffix is None or member.endswith(member_suffix)):
                yield member, archive.read(member)


def main():
    rel = sys.argv[1]
    kinds = sys.argv[2].split(",")
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    sub = sys.argv[4] if len(sys.argv) > 4 else None
    for member, data in load(rel):
        _, _, recs = AsmScan.records(data)
        shown = 0
        for index, rec in enumerate(recs):
            if rec["name"] not in kinds:
                continue
            text = " ".join(fmt(t, v) for t, v in rec["tokens"])
            if sub and sub not in text:
                continue
            print(member.rsplit("/", 1)[-1], index, rec["section"], rec["name"], len(rec["tokens"]))
            print("  ", text[:6000])
            shown += 1
            if shown >= limit:
                break


main()
