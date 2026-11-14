import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire


root = Path(__file__).resolve().parent
repository = root.parents[2]
inventory = json.loads((root.parent / "Reconstruction/CorpusInventory.json").read_text())
reflection = json.loads((root / "Reflection/Schema.json").read_text())
covered = {entry["metatype_identifier"].lower() for row in reflection["metatypes"] for entry in row["member_sets"] or [] if entry["initialized"] and entry["metatype_identifier"]}
archives = []
for row in inventory["files"]:
    path = repository / row["path"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
        raise ValueError("Corpus archive digest changed: " + row["path"])
    with ZipFile(path) as archive:
        wire = ReadMetaWire(archive.read(KDesignPrefix + "MetaStream.dat"))
    archives.append({**row, "classes": {entry.ClassGuid.lower() for entry in wire.Classes}})
universe = set().union(*(row["classes"] for row in archives))
initial = universe & covered
selected = []
while universe - covered:
    candidate = max(archives, key=lambda row: (len(row["classes"] - covered), -row["size"]))
    new = candidate["classes"] - covered
    if not new:
        raise ValueError("Greedy schema selection cannot cover remaining classes")
    selected.append({"path": candidate["path"], "sha256": candidate["sha256"], "size": candidate["size"], "new_declarations": sorted(new), "class_count": len(candidate["classes"])})
    covered |= candidate["classes"]
report = {"method": "Greedy coverage of corpus Design class declarations missing from the initial initialized runtime schema; largest uncovered gain, then smallest archive", "limitations": "Declaration coverage does not imply runtime initialization, acceptance or complete wire schema", "universe_count": len(universe), "initially_initialized_count": len(initial), "selected_count": len(selected), "selected": selected}
(root / "Reflection/Selection.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({key: value for key, value in report.items() if key != "selected"}))
