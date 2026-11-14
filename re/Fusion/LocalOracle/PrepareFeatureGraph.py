from dataclasses import replace
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.NumericParam import KParamGuid, ReadNativeNum
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.EmitSegment import EmitSegment
from convert.formats.Fusion.SegmentCodec.Features.ReadFeature import ReadFeature
from convert.formats.Fusion.SegmentCodec.Features.EmitFeature import EmitFeature
from convert.formats.Fusion.SegmentCodec.Features.Model.ClassStamp import ClassStamp
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire
from convert.formats.Fusion.SegmentCodec.Parameters.EmitNumeric import EmitNumeric
from convert.formats.Fusion.SegmentCodec.Parameters.EmitNumBinding import EmitNumBinding
from convert.formats.Fusion.SegmentCodec.Parameters.ReadNumBinding import ReadNumBinding


root = Path(__file__).resolve().parent / "Features"
source = root / "extrude_07mm.f3d"
destination = root / "kit_features_19mm.f3d"
changes = []
with ZipFile(source) as archive:
    bulk_name = KDesignPrefix + "BulkStream.dat"
    meta_name = KDesignPrefix + "MetaStream.dat"
    bulk = archive.read(bulk_name)
    meta = archive.read(meta_name)
    metadata = ReadMetaWire(meta)
    registry = {row.ClassGuid.upper(): row for row in metadata.Classes}
    spans = ReadBulkSpans(bulk, meta)
    feature_ids = {span.ObjectId for span in spans if span.IsPrimary and span.ClassGuid in ("8DA771B7-52ED-42FC-94E2-2353FE141373", "DD405BC2-D673-44F0-8833-5CB2A1C186C7")}
    records = []
    for span in spans:
        payload = bulk[span.PayloadOffset:span.EndOffset]
        if span.IsPrimary and span.ClassGuid == KParamGuid:
            value = ReadNativeNum(payload[4:])
            rewritten = value
            if value.ParamName == "depthLength":
                rewritten = replace(value, Number=1.9, Formula="19 mm", Comment="Kit native extrusion control rewrite")
            elif value.ParamName == "d2":
                rewritten = replace(value, Number=1.9)
            payload = EmitNumeric(rewritten)
            changes.append({"class": span.ClassGuid, "id": span.ObjectId, "parameter": value.ParamName, "before": value.Number, "after": rewritten.Number})
        elif span.IsPrimary and span.ClassGuid == "D91D429C-1BB5-4640-B49F-69AF14F463E9":
            value = ReadNumBinding(payload)
            rewritten = replace(value, Number=1.9) if value.ParamId == 243 else value
            payload = EmitNumBinding(rewritten)
            changes.append({"class": span.ClassGuid, "id": span.ObjectId, "parameter_id": value.ParamId, "before": value.Number, "after": rewritten.Number})
        elif span.ObjectId in feature_ids:
            lineage = []
            identity = span.ClassGuid
            while identity:
                row = registry[identity.upper()]
                lineage.append(ClassStamp(row.ClassGuid, row.BaseGuid, row.SchemaVersion))
                identity = row.BaseGuid
            feature = ReadFeature(payload, tuple(lineage))
            groups = tuple(replace(group, Fields=tuple(replace(field, Value="Kit ControlledExtrusion") if field.NameText == "featureUserName" and span.ClassGuid == "DD405BC2-D673-44F0-8833-5CB2A1C186C7" else field for field in group.Fields)) for group in feature.Groups)
            rewritten = replace(feature, Groups=groups)
            payload = EmitFeature(rewritten)
            changes.append({"class": span.ClassGuid, "id": span.ObjectId, "primary": span.IsPrimary, "operation": "full feature payload reconstructed from typed fields", "field_count": sum(len(group.Fields) for group in groups)})
        records.append(BulkRecord(span.TypeCode, span.ObjectId, span.IsPrimary, payload))
    new_bulk, new_meta = EmitSegment(metadata, records)
    with ZipFile(destination, "w") as target:
        for entry in archive.infolist():
            content = new_bulk if entry.filename == bulk_name else new_meta if entry.filename == meta_name else archive.read(entry)
            target.writestr(entry, content)
(root / "GraphRewrite.json").write_text(json.dumps({
    "source": source.name,
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "output": destination.name,
    "output_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
    "changes": changes,
    "scope": "Same-source native parameter/binding rewrite and complete sketch/extrusion/managed continuation serialization from typed fields, with new timeline names. Other source records and BRep caches retained. Geometry requires native rebuild; not independent document or BRep generation.",
}, indent=2) + "\n")
