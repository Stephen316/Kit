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
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire
from convert.formats.Fusion.SegmentCodec.Parameters.EmitNumeric import EmitNumeric
from convert.formats.Fusion.SegmentCodec.Parameters.EmitNumBinding import EmitNumBinding
from convert.formats.Fusion.SegmentCodec.Parameters.ReadNumBinding import ReadNumBinding


root = Path(__file__).resolve().parent / "Features"
source = root / "extrude_07mm.f3d"
destination = root / "kit_19mm.f3d"
changes = []
with ZipFile(source) as archive:
    bulk_name = KDesignPrefix + "BulkStream.dat"
    meta_name = KDesignPrefix + "MetaStream.dat"
    bulk = archive.read(bulk_name)
    meta = archive.read(meta_name)
    records = []
    for span in ReadBulkSpans(bulk, meta):
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
        records.append(BulkRecord(span.TypeCode, span.ObjectId, span.IsPrimary, payload))
    new_bulk, new_meta = EmitSegment(ReadMetaWire(meta), records)
    with ZipFile(destination, "w") as target:
        for entry in archive.infolist():
            content = new_bulk if entry.filename == bulk_name else new_meta if entry.filename == meta_name else archive.read(entry)
            target.writestr(entry, content)
(root / "Rewrite.json").write_text(json.dumps({
    "source": source.name,
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "output": destination.name,
    "output_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
    "changes": changes,
    "scope": "Same-source numeric parameter and binding rewrite. Existing feature records, history and BRep caches retained. Geometry requires native rebuild; not independent document or BRep generation.",
}, indent=2) + "\n")
