import hashlib
import json
import lzma
import runpy
import zipfile
from pathlib import Path


BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
GRAPH = runpy.run_path(str(BASE.parent / "EntityGraph/DecodeGraph.py"))
OGS = runpy.run_path(str(BASE.parent / "OgsScene/DecodeOgs.py"))


def inspect(source):
    path = ROOT / source
    graph = GRAPH["read_graph"](path)
    selected = []
    for row in graph["records"]:
        names = [graph["codec"].schema[group["identifier"].upper()]["name"] for group in row["value"]["groups"]]
        if any("mesh" in name.lower() for name in names):
            selected.append({**row, "classes": names})
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
    prefix = OGS["PREFIX"]
    world = OGS["API"]["archive_member"](path, prefix + "world")
    reader = OGS["Reader"](world)
    reason = None
    try:
        reader.world(root=True)
    except OGS["Unresolved"] as error:
        reason = str(error)
    return {
        "source": source, "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "record_count": len(graph["records"]), "mesh_records": selected,
        "world": {"bytes": len(world), "sha256": hashlib.sha256(world).hexdigest(),
                  "decoded_prefix": reader.offset, "unresolved": reason,
                  "fields": reader.fields},
        "members": [name for name in names if "ParaMesh" in name or "/OGS/" in name],
    }


def main():
    rows = json.loads((BASE / "ContainerFields.json").read_text())["containers"]
    sources = list(dict.fromkeys((rows[0]["archive"], max(rows, key=lambda row: row["vertices"])["archive"])))
    report = {"scope": "Independent read-only research decoding; no production codec or native application execution", "sources": [inspect(source) for source in sources]}
    payload = lzma.compress((json.dumps(report, indent=2) + "\n").encode())
    (BASE / "DocumentLinks.json.xz").write_bytes(payload)
    summary = {"details": "DocumentLinks.json.xz", "sha256": hashlib.sha256(payload).hexdigest(), "sources": [{"source": row["source"], "record_count": row["record_count"], "mesh_records": len(row["mesh_records"]), "world_bytes": row["world"]["bytes"], "decoded_prefix": row["world"]["decoded_prefix"], "unresolved": row["world"]["unresolved"]} for row in report["sources"]]}
    (BASE / "DocumentLinks.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
