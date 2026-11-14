import hashlib
import json
from pathlib import Path
import runpy
import sys
from zipfile import ZipFile

root = Path(__file__).resolve().parent
repository = root.parents[2]
sys.path.insert(0, str(repository / "src"))

from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.EmitSegment import EmitSegment
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire

api = runpy.run_path(str(repository / "re/Fusion/Reconstruction/EntityGraph/DecodeGraph.py"))
source = root / "Features/kit_features_19mm.f3d"
output = root / "Features/kit_cached_19mm.f3d"
geometry = repository / "re/Fusion/Reconstruction/BrepHistory/IndependentNineteen.smbh"
graph = api["read_graph"](source)
with ZipFile(source) as archive:
    bulk_name = KDesignPrefix + "BulkStream.dat"
    meta_name = KDesignPrefix + "MetaStream.dat"
    bulk = archive.read(bulk_name)
    meta = archive.read(meta_name)
    spans = ReadBulkSpans(bulk, meta)
    records = []
    for span, value in zip(spans, graph["records"], strict=True):
        if span.ObjectId != value["identity"] or span.IsPrimary != value["primary"] or span.PayloadOffset != value["payloadBulkOffset"]:
            raise RuntimeError("Typed graph identity mismatch")
        payload = api["emit_record"](graph["codec"], json.loads(json.dumps(value["value"])), value["primary"])
        if payload != bulk[span.PayloadOffset:span.EndOffset]:
            raise RuntimeError("Unedited complete graph reconstruction differs")
        records.append(BulkRecord(span.TypeCode, span.ObjectId, span.IsPrimary, payload))
    new_bulk, new_meta = EmitSegment(ReadMetaWire(meta), records)
    geometry_names = [name for name in archive.namelist() if name.endswith(".smbh")]
    if len(geometry_names) != 1:
        raise RuntimeError("Expected one solved geometry history member")
    replacements = {bulk_name: new_bulk, meta_name: new_meta, geometry_names[0]: geometry.read_bytes()}
    with ZipFile(output, "w") as target:
        for entry in archive.infolist():
            target.writestr(entry, replacements.get(entry.filename, archive.read(entry)))
report = {"source": source.name, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "output": output.name, "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "reconstructed_design_records": len(records), "independent_geometry_sha256": hashlib.sha256(geometry.read_bytes()).hexdigest(), "replaced_members": list(replacements), "scope": "Same-source complete Design record reconstruction from typed fields plus independently authored solved cylinder and insertion journal; other source members retained; not independent full document generation"}
(root / "Features/CacheRewrite.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
