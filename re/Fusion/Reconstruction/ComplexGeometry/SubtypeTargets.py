import collections
import json
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.ListSubtypes import ListSubtypes  # noqa: E402


def main():
    verify = json.loads((BASE / "VerifyComplex.json").read_text())
    targets = collections.Counter()
    members = collections.Counter()
    for member in verify["members"]:
        if member["status"] != "exact":
            continue
        with zipfile.ZipFile(ROOT / member["path"]) as archive:
            payload = archive.read(member["member"])
        model = ReadJournal(payload) if member["member"].endswith(".smbh") else ReadGeometry(payload)
        table = []
        seen = set()
        for entity in model.Entities:
            for name, index in ListSubtypes(entity):
                if index is None:
                    table.append(name)
                    continue
                key = name + " -> " + table[index]
                targets[key] += 1
                seen.add(key)
        for key in seen:
            members[key] += 1
    rows = [dict(reference=key, count=count, members=members[key]) for key, count in sorted(targets.items(), key=lambda item: (-item[1], item[0]))]
    report = dict(
        script="re/Fusion/Reconstruction/ComplexGeometry/SubtypeTargets.py",
        scope="every subtype reference in the exact complex members of VerifyComplex.json",
        reference="reference family -> subtype name of the stream-global table entry it indexes",
        rows=rows,
    )
    (BASE / "SubtypeTargets.json").write_text(json.dumps(report, indent=1) + "\n")
    for row in rows:
        print(row["count"], row["members"], row["reference"])


main()
