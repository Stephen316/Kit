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

prep = json.loads((ROOT / "re/Fusion/LocalOracle/ComplexGeometry/Preparation.json").read_text())
overall = collections.Counter()
rows = []
for section in ("authored", "geometry", "edited", "histories"):
    for item in prep[section]:
        names = collections.Counter()
        paths = []
        if section == "histories":
            with zipfile.ZipFile(ROOT / item["target"]) as archive:
                for member in item["members"]:
                    payload = archive.read(member["member"])
                    model = ReadJournal(payload) if member["member"].endswith(".smbh") else ReadGeometry(payload)
                    paths.append((member["kind"], model))
        else:
            payload = (ROOT / item["target"]).read_bytes()
            paths.append(("snapshot", ReadGeometry(payload)))
            if "history" in item:
                paths.append(("history", ReadJournal((ROOT / item["history"]).read_bytes())))
        for kind, model in paths:
            for value in model.Entities:
                for name, index in ListSubtypes(value):
                    key = kind + ":" + (name if index is None else "ref:" + name)
                    names[key] += 1
                    overall[name if index is None else "ref:" + name] += 1
        rows.append(dict(section=section, label=item["label"], subtypes=dict(sorted(names.items()))))
        print(section, item["label"], dict(sorted(names.items())))
print("overall", dict(sorted(overall.items())))
(BASE / "NativeCoverage.json").write_text(json.dumps(dict(script="re/Fusion/Reconstruction/ComplexGeometry/NativeCoverage.py", scope="subtype definitions and references in every member that the native acceptance opened", rows=rows, overall=dict(sorted(overall.items()))), indent=1) + "\n")
