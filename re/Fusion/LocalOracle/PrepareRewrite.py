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


root = Path(__file__).resolve().parent
source = root / "Allocation/added_third.f3d"
output = root / "Rewritten"
output.mkdir(exist_ok=True)
destination = output / "edited_parameters.f3d"
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
            requested = {"betaLength": (3.1, "31 mm"), "gammaLength": (4.7, "47 mm")}[value.ParamName]
            rewritten = replace(value, Number=requested[0], Formula=requested[1], Comment="Written by Kit native parameter codec")
            payload = EmitNumeric(rewritten)
            changes.append({"name": value.ParamName, "before": value.Number, "after": rewritten.Number, "creation_index": value.NativeIndex})
        records.append(BulkRecord(span.TypeCode, span.ObjectId, span.IsPrimary, payload))
    new_bulk, new_meta = EmitSegment(ReadMetaWire(meta), records)
    with ZipFile(destination, "w") as target:
        for entry in archive.infolist():
            content = new_bulk if entry.filename == bulk_name else new_meta if entry.filename == meta_name else archive.read(entry)
            target.writestr(entry, content)
(output / "Rewrite.json").write_text(json.dumps({
    "source": str(source.relative_to(root)),
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "output": destination.name,
    "output_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
    "changes": changes,
    "scope": "Native numeric parameter edits in the same source archive; other source records retained. Not independent complete document generation.",
}, indent=2) + "\n")
