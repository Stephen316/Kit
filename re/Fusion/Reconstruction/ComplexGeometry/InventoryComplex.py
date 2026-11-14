import collections
import hashlib
import json
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(ROOT / "src"))

import AsmScan  # noqa: E402

from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry  # noqa: E402

KNOWN = {
    "asmheader", "body", "lump", "shell", "face", "loop", "coedge", "edge", "vertex", "point",
    "plane-surface", "cone-surface", "sphere-surface", "torus-surface", "straight-curve",
    "ellipse-curve", "transform", "ATTRIB_CUSTOM-attrib", "history_stream", "delta_state",
}
GEOM = ("spline-surface", "intcurve-curve", "pcurve")


def signature(rec):
    tree = AsmScan.subtree(rec["tokens"])
    names = AsmScan.subnames(tree)
    top = next((label for depth, label in names if depth == 0), None)
    nested = sorted({label for depth, label in names if depth > 0 and label})
    return top, nested


def main():
    inventory = json.loads((ROOT / "re/Fusion/Reconstruction/CorpusInventory.json").read_text())
    seen = {}
    rows = []
    for item in inventory["files"]:
        path = ROOT / item["path"]
        try:
            archive = zipfile.ZipFile(path)
        except Exception as error:
            rows.append({"path": item["path"], "error": repr(error)})
            continue
        with archive:
            for member in archive.namelist():
                if not member.endswith((".smb", ".smbh")):
                    continue
                data = archive.read(member)
                digest = hashlib.sha256(data).hexdigest()
                row = {"path": item["path"], "member": member, "sha256": digest, "size": len(data)}
                rows.append(row)
                if digest in seen:
                    row["duplicateOf"] = seen[digest]
                    continue
                seen[digest] = len(rows) - 1
                try:
                    words, head, recs = AsmScan.records(data)
                except Exception as error:
                    row["scanError"] = repr(error)
                    continue
                names = collections.Counter((rec["section"], rec["name"]) for rec in recs)
                row["names"] = {f"{s}:{n}": c for (s, n), c in sorted(names.items())}
                unknown = sorted({rec["name"] for rec in recs} - KNOWN)
                row["unsupportedNames"] = unknown
                subtypes = collections.Counter()
                nested = collections.Counter()
                for rec in recs:
                    if rec["name"] in GEOM:
                        top, inner = signature(rec)
                        subtypes[f"{rec['name']}:{top}"] += 1
                        for label in inner:
                            nested[f"{rec['name']}:{top}>{label}"] += 1
                row["subtypes"] = dict(subtypes)
                row["nested"] = dict(nested)
                row["tags"] = sorted({tag for rec in recs for tag, _ in rec["tokens"]})
                try:
                    if member.endswith(".smbh"):
                        ReadJournal(data)
                    else:
                        ReadGeometry(data)
                    row["production"] = "ok"
                except Exception as error:
                    row["production"] = str(error)[:160]
    out = BASE / "Inventory.json"
    out.write_text(json.dumps(rows, indent=0, sort_keys=True))
    unique = [row for row in rows if "names" in row]
    summary = {
        "members": len([row for row in rows if "member" in row]),
        "uniqueMembers": len(unique),
        "scanErrors": [row for row in rows if "scanError" in row],
        "production": collections.Counter(row["production"] for row in unique).most_common(),
    }
    names = collections.Counter()
    subtypes = collections.Counter()
    nested = collections.Counter()
    members_with = collections.Counter()
    for row in unique:
        for key, count in row["names"].items():
            names[key] += count
        for key, count in row["subtypes"].items():
            subtypes[key] += count
            members_with[key] += 1
        for key, count in row["nested"].items():
            nested[key] += count
    summary["names"] = names.most_common()
    summary["subtypes"] = subtypes.most_common()
    summary["subtypeMembers"] = members_with.most_common()
    summary["nested"] = nested.most_common()
    summary["tags"] = collections.Counter(tag for row in unique for tag in row["tags"]).most_common()
    (BASE / "InventorySummary.json").write_text(json.dumps(summary, indent=1))


main()
