import hashlib
import json
import lzma
import struct
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
SOURCE = (ROOT / "InspectContainers.py").read_text().split("\ninventory =")[0]
RESEARCH = {"__file__": str(ROOT / "InspectContainers.py")}
exec(compile(SOURCE, str(ROOT / "InspectContainers.py"), "exec"), RESEARCH)


def semantic_value(payload):
    report = RESEARCH["inspect"](payload)
    cursor = RESEARCH["Cursor"](payload)
    cursor.take(48)
    length = cursor.integer(8)
    cursor.integer(4)
    cursor.take(length)
    length = cursor.integer(8)
    cursor.integer(4)
    cursor.take(length)
    names = sorted(report["name_table"], key=report["name_table"].get)
    streams = {}
    for name in names:
        length = cursor.integer(8)
        assert cursor.integer(4) == 4
        _, streams[name] = RESEARCH["stream"](cursor.take(length))
    metadata = report["registry"]
    normal, groups = metadata["channels"]
    registry = {
        "MeshId": metadata["mesh_uuid"],
        "FusionId": metadata["properties"][0]["text"],
        "NormalId": normal["resource_guid"],
        "FaceGroupCount": metadata["face_group_count"],
        "VertexStream": metadata["vertices"],
        "CornerStream": metadata["triangles"],
        "NormalStream": normal["streams"]["values"],
        "OverrideStream": normal["streams"]["index"],
        "EdgeStream": metadata["feature_edges"][0]["4"],
        "GroupStream": groups["streams"]["values"],
        "Groups": [{"GroupKey": item["key"], "GroupId": item["guid"]} for item in groups["groups"]],
        "StreamOrder": names,
    }
    points = [{"XCoord": x, "YCoord": y, "ZCoord": z} for x, y, z in struct.iter_unpack("<fff", streams[metadata["vertices"]])]
    differences = [item[0] for item in struct.iter_unpack("<i", streams[metadata["triangles"]])]
    corners = [report["first_corner"]]
    for difference in differences[:-1]:
        corners.append(corners[-1] + difference)
    terminals = RESEARCH["terminal_values"]
    edges = terminals(streams[registry["EdgeStream"]])
    return {
        "Registry": registry,
        "Positions": points,
        "Corners": corners,
        "TerminalWord": differences[-1],
        "Normals": [{"First": x, "Second": y} for x, y in struct.iter_unpack("<ff", streams[registry["NormalStream"]])],
        "Overrides": terminals(streams[registry["OverrideStream"]]),
        "Edges": [{"First": edges[index], "Second": edges[index + 1]} for index in range(0, len(edges), 2)],
        "FaceGroups": terminals(streams[registry["GroupStream"]]),
    }


def main():
    inventory = json.loads((ROOT / "CorpusInventory.json").read_text())
    cases = []
    for archive in inventory["archives"]:
        source = (REPO / archive["archive"]).read_bytes()
        with zipfile.ZipFile(REPO / archive["archive"]) as container:
            for member in archive["members"]:
                payload = container.read(member["name"])
                model = semantic_value(payload)
                encoded = json.dumps(model, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
                cases.append({
                    "Archive": archive["archive"], "Member": member["name"],
                    "SourceHash": hashlib.sha256(source).hexdigest(),
                    "PayloadHash": hashlib.sha256(payload).hexdigest(),
                    "SemanticHash": hashlib.sha256(encoded).hexdigest(),
                    "Vertices": len(model["Positions"]), "Triangles": len(model["Corners"]) // 3,
                })
    output = REPO / "tests/convert/formats/FusionCodec/Mesh/MeshSources.xz"
    output.parent.mkdir(parents=True, exist_ok=True)
    data = lzma.compress((json.dumps(cases, indent=2) + "\n").encode())
    output.write_bytes(data)
    print(json.dumps({"cases": len(cases), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}))


if __name__ == "__main__":
    main()
