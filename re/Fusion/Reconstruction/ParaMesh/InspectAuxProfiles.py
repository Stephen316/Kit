import hashlib
import json
import runpy
from pathlib import Path


BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
TOOLS = runpy.run_path(str(BASE.parent / "ReflectedFeatures.py"))


def classes(payload):
    reader = TOOLS["Reader"](payload)
    reader.text()
    reader.number("I")
    reader.text(True)
    reader.take(16)
    reader.text()
    reader.text()
    reader.take(8)
    result = []
    for _ in range(reader.count()):
        guid, base = reader.text(), reader.text()
        version, namespace = reader.number("I"), reader.text()
        owners = [reader.number("Q") for _ in range(reader.count())]
        result.append({"ClassGuid": guid, "BaseGuid": base, "SchemaVersion": version, "OwnerCount": len(owners)})
    return result


def main():
    known = {}
    for relative in ("DocumentCodec/Vocabulary/DesignClasses.json", "ContainerCodec/Assembly/ActClasses.json", "ContainerCodec/Browser/BrowserClasses.json"):
        for row in json.loads((ROOT / "src/convert/formats/Fusion" / relative).read_bytes()):
            known[row["ClassGuid"].upper()] = row
    known["75CB256B-FDDE-44D6-AE08-4DB583875AB7"] = {"ClassGuid": "75CB256B-FDDE-44D6-AE08-4DB583875AB7", "BaseGuid": "6AE9DE8C-A6F6-40CB-B13D-4091AEA4968D", "SchemaVersion": 0}
    sources = sorted({row["archive"] for row in json.loads((BASE / "ContainerFields.json").read_text())["containers"]})
    rows = []
    for source in sources:
        for kind in ("FusionACTSegmentType", "FusionBrowserSegmentType"):
            member = f"FusionAssetName[Active]/{kind}1/MetaStream.dat"
            payload = TOOLS["archive_member"](ROOT / source, member)
            missing = []
            entries = classes(payload)
            for row in entries:
                previous = known.get(row["ClassGuid"].upper())
                if previous is None or previous["SchemaVersion"] != row["SchemaVersion"] or previous["BaseGuid"].upper() != row["BaseGuid"].upper():
                    missing.append(row)
            rows.append({"source": source, "member": member, "metadata_sha256": hashlib.sha256(payload).hexdigest(), "class_count": len(entries), "differences": missing})
    report = {"scope": "Raw metadata schema comparison only, no production/native execution", "segments": len(rows), "differing_segments": sum(bool(row["differences"]) for row in rows), "rows": rows}
    (BASE / "AuxiliaryProfiles.json").write_text(json.dumps(report, indent=2) + "\n")
    unique = {json.dumps(row, sort_keys=True) for segment in rows for row in segment["differences"]}
    print(json.dumps({"segments": len(rows), "differences": [json.loads(value) for value in sorted(unique)]}, indent=2))


if __name__ == "__main__":
    main()
