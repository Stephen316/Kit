import dataclasses
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))
sys.dont_write_bytecode = True

from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.EntityCodec.DecodeEntities import DecodeEntities
from convert.formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.formats.Fusion.DocumentCodec.Records.MakeDesignProf import MakeDesignProf
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire

import convert.formats.Fusion.EntityCodec.Values.ReadShapeMut as ShapeModule
from convert.formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Wire.ReadAtomMut import ReadAtomMut


def permissive_matrix(cursor, shape):
    if ReadAtomMut(cursor, WireType("bool")):
        return MatrixValue(None)
    return MatrixValue(tuple(float(ReadAtomMut(cursor, WireType("f64"))) for _ in range(16)))


ShapeModule.ReadMatrixMut = permissive_matrix
NAMES = {}
for entry in json.loads((REPO / "re/Fusion/Reconstruction/BinaryClasses.json").read_text())["classes"]:
    NAMES.setdefault(entry["identifier"].upper(), entry["class"].split("::")[-1])
for vocab in (REPO / "src/convert/formats/Fusion/DocumentCodec").rglob("*Classes.json"):
    for entry in json.loads(vocab.read_text()):
        NAMES.setdefault(entry["ClassGuid"].upper(), entry["NameValue"])


def name_of(guid):
    return NAMES.get(guid.upper(), guid)


def plain(value):
    if dataclasses.is_dataclass(value):
        kind = type(value).__name__
        if kind == "LocalRef":
            return {"ref": value.ObjectId}
        if kind == "SegmentRef":
            return {"ref": value.ObjectId, "segment": value.SegmentId}
        if kind == "EntityGroup":
            return {"class": name_of(value.ClassGuid), "fields": {f.FieldName: plain(f.Value) for f in value.Fields}}
        if kind == "ValueObject":
            return {"object": [plain(g) for g in value.Groups]}
        if kind == "ValueSeries":
            return [plain(v) for v in value.Items]
        if kind == "ValueMap":
            return {"map": [[plain(p.First), plain(p.Second)] for p in value.Entries]}
        if kind == "ValuePair":
            return [plain(value.First), plain(value.Second)]
        if kind == "OptionalValue":
            return {"optional": plain(value.Value)}
        result = {"$": kind}
        for field in dataclasses.fields(value):
            result[field.name] = plain(getattr(value, field.name))
        return result
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, float) and value != value:
        return "nan"
    return value


def decode(path, prefix):
    with OpenFusionZip(path.read_bytes()) as archive:
        members = [m.Name for m in archive.Members]
        design_meta = next(n for n in members if n.endswith("MetaStream.dat") and prefix in n)
        design_bulk = design_meta.replace("MetaStream.dat", "BulkStream.dat")
        bulk = archive.ReadMember(design_bulk, 1 << 26)
        meta = archive.ReadMember(design_meta, 1 << 26)
        others = [ReadMetaWire(archive.ReadMember(n, 1 << 26)) for n in members if n.endswith("MetaStream.dat") and n != design_meta]
        parts = {m.Name: m.UncompressedSize if hasattr(m, "UncompressedSize") else None for m in archive.Members}
    metadata = ReadMetaWire(meta)
    targets = tuple(ExternalTarget(s.Header.SegmentId, oid, e.ClassGuid) for s in others for e in s.Classes for oid in e.OwnerIds)
    records = tuple(BulkRecord(s.TypeCode, s.ObjectId, s.IsPrimary, bulk[s.PayloadOffset:s.EndOffset]) for s in ReadBulkSpans(bulk, meta))
    profile = MakeDesignProf(ReadDocSchemas(), metadata.Classes, targets)
    model = DecodeEntities(records, metadata.Classes, profile)
    codes = {}
    for index, entry in enumerate(metadata.Classes):
        codes[256 + index] = entry
    entities = {}
    for record in model:
        key = record.ObjectId
        item = entities.setdefault(key, {"id": key, "class": None, "rootId": "", "subjects": None, "groups": []})
        if record.IsPrimary:
            item["class"] = name_of(record.Groups[0].ClassGuid)
            item["rootId"] = record.Frame.RootId
            item["subjects"] = None if record.Frame.Subjects is None else [[plain(s.Target), s.ObserverIndex] for s in record.Frame.Subjects]
            item["named"] = None if record.Frame.Metadata is None else [plain(m) for m in record.Frame.Metadata]
        item["groups"].extend(plain(g) for g in record.Groups)
    return {"members": members, "classes": [{"class": name_of(c.ClassGuid), "guid": c.ClassGuid, "version": c.SchemaVersion, "count": len(c.OwnerIds)} for c in metadata.Classes], "next_id": metadata.NextObjectId if hasattr(metadata, "NextObjectId") else None, "entities": [entities[k] for k in sorted(entities)]}


if __name__ == "__main__":
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    output.mkdir(parents=True, exist_ok=True)
    summary = {}
    for path in sorted(source.glob("*.f3d")):
        try:
            result = {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            result["design"] = decode(path, "FusionDesignSegmentType")
            (output / (path.stem + ".json")).write_text(json.dumps(result, indent=1) + "\n")
            summary[path.stem] = {"entities": len(result["design"]["entities"]), "classes": len(result["design"]["classes"])}
        except Exception as error:
            summary[path.stem] = {"error": repr(error)[:400]}
        print(path.stem, summary[path.stem], flush=True)
    (output / "Summary.json").write_text(json.dumps(summary, indent=1) + "\n")
