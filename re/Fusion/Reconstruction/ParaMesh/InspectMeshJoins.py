import hashlib
import json
import lzma
import runpy
from pathlib import Path


BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
GRAPH = runpy.run_path(str(BASE.parent / "EntityGraph/DecodeGraph.py"))
OGS = runpy.run_path(str(BASE.parent / "OgsScene/DecodeOgs.py"))
GEOMETRY = "A8338A26-5436-433C-8BAC-C3CF024AD595"
TRIGGER = "A1BAA3F6-4B67-4A0D-BACC-75F38A2230F3"
BLOB = "130A0711-4E92-4FCD-AADE-B9C82238BB27"
BODY = "EA90DA22-556C-4C61-89BB-20C2681B7A9D"


def inspect(source, parts):
    path = ROOT / source
    graph = GRAPH["read_graph"](path)
    records = {row["identity"]: {group["identifier"].upper(): group["fields"] for group in row["value"]["groups"]} for row in graph["records"] if row["primary"]}
    joins, bodies, errors = [], [], []
    for identity, groups in records.items():
        if BODY in groups:
            fields = groups[BODY]
            bodies.append({"body": identity, "geometry": fields["rMeshGeometry"], "feature": fields["rDcFeature"], "transform": fields["mtxTransform"], "baked_transform": fields["mtxBakedTransform"]})
        if GEOMETRY not in groups:
            continue
        fields = groups[GEOMETRY]
        trigger_id = fields["rSerializerTrigger"]["entityId"]
        trigger = records[trigger_id]
        member = "FusionAssetName[Active]/ParaMeshGeometry.BlobParts/" + trigger[BLOB]["partName"]
        part = next((part for part in parts if part["member"] == member), None)
        fusion_id = next((item["text"] for item in part["registry"]["properties"] if item["key"] == "fusion_uuid"), None) if part else None
        reciprocal = trigger[TRIGGER]["rMeshGeometry"] == {"entityId": identity}
        if not reciprocal or fusion_id != fields["pMeshUuid"]:
            errors.append({"geometry": identity, "reciprocal": reciprocal, "part_found": part is not None, "uuid_matches": fusion_id == fields["pMeshUuid"]})
        joins.append({"geometry": identity, "trigger": trigger_id, "member": member, "fusion_uuid": fields["pMeshUuid"], "identity_volume": fields["identityVolume"], "is_closed": fields["isClosed"], "is_oriented": fields["isOriented"], "needs_update": fields["needsUpdate"], "texture_mapping_count": len(fields["textureIdToUuidMap"])})
    addressed = [row["member"] for row in joins]
    if len(set(addressed)) != len(addressed) or set(addressed) != {part["member"] for part in parts}:
        errors.append({"component_inventory_differs": True})
    world = OGS["API"]["archive_member"](path, OGS["PREFIX"] + "world")
    reader = OGS["Reader"](world)
    reason = None
    try:
        reader.world(root=True)
        if reader.offset != len(world):
            reason = "Trailing world bytes"
    except Exception as error:
        reason = str(error)
    return {"source": source, "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "joins": joins, "bodies": bodies, "errors": errors, "world": {"bytes": len(world), "sha256": hashlib.sha256(world).hexdigest(), "consumed": reader.offset, "unresolved": reason}}


def main():
    inventory = json.loads(lzma.decompress((BASE / "ContainerFields.json.xz").read_bytes()))["containers"]
    sources = sorted({row["archive"] for row in inventory})
    rows = [inspect(source, [row for row in inventory if row["archive"] == source]) for source in sources]
    report = {"scope": "Read-only graph-to-container identity and ordinary-world inspection; no production/native execution", "archives": rows}
    data = lzma.compress((json.dumps(report, indent=2) + "\n").encode())
    (BASE / "MeshJoins.json.xz").write_bytes(data)
    summary = {"details": "MeshJoins.json.xz", "sha256": hashlib.sha256(data).hexdigest(), "archives": len(rows), "mesh_geometry_joins": sum(len(row["joins"]) for row in rows), "mesh_bodies": sum(len(row["bodies"]) for row in rows), "join_errors": sum(len(row["errors"]) for row in rows), "worlds_fully_consumed": sum(row["world"]["unresolved"] is None for row in rows), "unresolved_worlds": [{"source": row["source"], "world": row["world"]} for row in rows if row["world"]["unresolved"] is not None]}
    (BASE / "MeshJoins.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
