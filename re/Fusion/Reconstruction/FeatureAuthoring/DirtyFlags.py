import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))
sys.dont_write_bytecode = True

from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.DocumentCodec.Records.MakeDesignProf import MakeDesignProf
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.formats.Fusion.EntityCodec.DecodeEntities import DecodeEntities
from convert.formats.Fusion.EntityCodec.EncodeEntities import EncodeEntities
from convert.formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.EmitSegment import EmitSegment
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire

DESIGN = "FusionAssetName[Active]/FusionDesignSegmentType1/"
NAMES = {}
for entry in json.loads((REPO / "re/Fusion/Reconstruction/BinaryClasses.json").read_text())["classes"]:
    NAMES.setdefault(entry["identifier"].upper(), entry["class"].split("::")[-1])
for vocab in (REPO / "src/convert/formats/Fusion/DocumentCodec").rglob("*Classes.json"):
    for entry in json.loads(vocab.read_text()):
        NAMES.setdefault(entry["ClassGuid"].upper(), entry["NameValue"])


def load(archive):
    bulk = archive.read(DESIGN + "BulkStream.dat")
    meta = archive.read(DESIGN + "MetaStream.dat")
    others = [ReadMetaWire(archive.read(n)) for n in archive.namelist() if n.endswith("MetaStream.dat") and not n.startswith(DESIGN)]
    metadata = ReadMetaWire(meta)
    targets = tuple(ExternalTarget(s.Header.SegmentId, oid, e.ClassGuid) for s in others for e in s.Classes for oid in e.OwnerIds)
    records = tuple(BulkRecord(s.TypeCode, s.ObjectId, s.IsPrimary, bulk[s.PayloadOffset:s.EndOffset]) for s in ReadBulkSpans(bulk, meta))
    profile = MakeDesignProf(ReadDocSchemas(), metadata.Classes, targets)
    return metadata, profile, list(DecodeEntities(records, metadata.Classes, profile))


def class_of(record):
    return NAMES.get(record.Groups[0].ClassGuid.upper(), "")


def set_field(record, group_name, **fields):
    groups = []
    hit = False
    for group in record.Groups:
        if NAMES.get(group.ClassGuid.upper()) == group_name:
            values = []
            for named in group.Fields:
                if named.FieldName in fields:
                    values.append(NamedValue(named.FieldName, fields[named.FieldName]))
                    hit = True
                else:
                    values.append(named)
            group = replace(group, Fields=tuple(values))
        groups.append(group)
    if not hit:
        raise ValueError("Field not found " + group_name + repr(fields))
    return replace(record, Groups=tuple(groups))


def field(record, group_name, name):
    for group in record.Groups:
        if NAMES.get(group.ClassGuid.upper()) == group_name:
            for named in group.Fields:
                if named.FieldName == name:
                    return named.Value
    raise KeyError(name)


def feature_ids(records, feature_class):
    return [r.ObjectId for r in records if r.IsPrimary and class_of(r) == feature_class]


def variant(records, feature_class, mode):
    target = feature_ids(records, feature_class)[0]
    by_id = {}
    for index, r in enumerate(records):
        if r.IsPrimary:
            by_id[r.ObjectId] = index
    owned = {target}
    for index, r in enumerate(records):
        if r.IsPrimary and class_of(r) in ("DcDoubleParameter", "ModelDataRef", "BrepRef", "DRBody"):
            try:
                parent = field(r, "DcNode", "rParentFeature")
            except KeyError:
                continue
            if parent is not None and parent.ObjectId == target:
                owned.add(r.ObjectId)
    for index, r in enumerate(records):
        if not r.IsPrimary:
            continue
        name = class_of(r)
        if mode in ("update", "all") and name == "DynamicUpdateData" and field(r, "DynamicUpdateData", "rOwnerNode") is not None and field(r, "DynamicUpdateData", "rOwnerNode").ObjectId in owned:
            records[index] = set_field(r, "DynamicUpdateData", isBodyOK=False, isPredecessorOK=False, predecessors=ValueMap(()), timeStamp=0)
        if mode in ("edited", "all") and r.ObjectId == target:
            records[index] = set_field(records[index], "DcNode", isEdited=True)
        if mode in ("sort", "all") and name == "DcComputeManager":
            records[index] = set_field(r, "DcComputeManager", sortIsCurrent=False)
        if mode in ("sort", "all") and name == "DcDependencyManager":
            records[index] = set_field(r, "DcDependencyManager", mapsAreCurrent=False)
        if mode in ("param", "all") and name == "Parameter":
            dc = field(r, "Parameter", "dcParameter")
            if dc is not None and dc.ObjectId in owned:
                records[index] = set_field(r, "Parameter", isDirty=True)
    return records


def write(source, target, feature_class, mode):
    with ZipFile(source) as archive:
        metadata, profile, records = load(archive)
        records = variant(records, feature_class, mode)
        encoded = EncodeEntities(tuple(records), metadata.Classes, profile)
        bulk, meta = EmitSegment(metadata, encoded)
        with ZipFile(target, "w", compression=ZIP_DEFLATED) as output:
            for entry in archive.infolist():
                data = archive.read(entry.filename)
                if entry.filename == DESIGN + "BulkStream.dat":
                    data = bulk
                elif entry.filename == DESIGN + "MetaStream.dat":
                    data = meta
                if entry.is_dir():
                    output.writestr(entry, b"")
                else:
                    output.writestr(entry.filename, data)
    return {"name": target.stem, "source": source.name, "target": target.name, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "target_sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "feature": feature_class, "mode": mode}


if __name__ == "__main__":
    folder = REPO / "re/Fusion/LocalOracle/FeatureAuthoring/Recompute"
    report = {"scope": "Truncated-journal fillet control with explicit persisted dirty-state edits on the unsolved feature; tests whether any saved state triggers regeneration on open", "cases": []}
    for mode in ("update", "edited", "sort", "param", "all"):
        entry = write(folder / "FilletWithoutFilletState.f3d", folder / ("FilletDirty" + mode.capitalize() + ".f3d"), "DcFilletEdgeFeature", mode)
        entry["source"] = "Fillet.f3d"
        report["cases"].append(entry)
        print(entry["name"], entry["target_sha256"])
    (folder / "DirtyPreparation.json").write_text(json.dumps(report, indent=2) + "\n")
