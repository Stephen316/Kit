import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from ExampleRecords import documents, segments
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.Records.MakeDocProfile import MakeDocProfile
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.formats.Fusion.EntityCodec.Records.BindRecords import BindRecords
from convert.formats.Fusion.EntityCodec.Records.ReadEntity import ReadSlack
from convert.formats.Fusion.EntityCodec.Schema.BindProfile import BindProfile
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire
from convert.formats.Fusion.BulkSpans import ReadBulkSpans


def main():
    wanted = sys.argv[1]
    prefix = sys.argv[2].upper()
    for name, data in documents():
        if not name.endswith(wanted):
            continue
        container = ReadContainer(data)
        schemas = ReadDocSchemas()
        metas = tuple(ReadMetaWire(stream.Metadata, Segment=slot.Segment) for stream, slot in zip(container.Streams, container.Asset.Segments, strict=True))
        for stream, meta in zip(container.Streams, metas, strict=True):
            profile = MakeDocProfile(schemas, metas, stream.SegmentId)
            catalog = BindProfile(profile, meta.Classes)
            spans = list(ReadBulkSpans(stream.BulkData, stream.Metadata, Segment=meta.Header.Segment))
            items = tuple(BulkRecord(span.TypeCode, span.ObjectId, span.IsPrimary, stream.BulkData[span.PayloadOffset:span.EndOffset]) for span in spans)
            scope = BindRecords(items, meta.Classes)
            for span, item in zip(spans, items):
                if not span.ClassGuid.upper().startswith(prefix):
                    continue
                value, slack = ReadSlack(item, scope, catalog)
                if not slack:
                    continue
                print(meta.Header.Segment.name, span.ObjectId, len(item.Payload), len(slack))
                guid = span.ClassGuid.upper()
                while guid in catalog.Classes:
                    schema = catalog.Classes[guid]
                    row = next((row for row in meta.Classes if row.ClassGuid.upper() == guid), None)
                    print(' ', guid[:8], 'v', schema.SchemaVersion, 'opaque' if schema.IsOpaque else '', 'meta', None if row is None else (row.SchemaVersion, row.BaseGuid[:8]), len(schema.Members))
                    guid = schema.BaseGuid.upper()
                for group in value.Groups:
                    print('  group', group.ClassGuid[:8], [(field.FieldName, type(field.Value).__name__, len(getattr(field.Value, 'Items', ()) or ())) for field in group.Fields])
                used = len(item.Payload) - len(slack)
                print('  used tail', item.Payload[max(0, used - 32):used].hex())
                print('  slack head', slack[:64].hex())
                bulk = stream.BulkData
                start = len(bulk) - len(slack)
                for size in (16, 32, 64):
                    hits = [index for index in range(len(bulk)) if bulk.startswith(slack[:size], index) and index != start]
                    print('  copies of first', size, 'bytes at', hits[:5], 'record starts', [span.PayloadOffset for span in spans][:3], 'bulk', len(bulk))
                print('  zero share', round(slack.count(0) / len(slack), 2))
                owners = sorted(oid for row in meta.Classes for oid in row.OwnerIds)
                indexed = sorted(span.ObjectId for span in spans if span.IsPrimary)
                print('  owners', len(owners), 'primary spans', len(indexed), 'spans', len(spans), 'missing', sorted(set(owners) - set(indexed))[:10], 'max owner', owners[-1] if owners else None)
                for offset in (4237, 4352, 4467, 4582, 4697, 4812):
                    print('  at', offset, bulk[offset:offset + 15].hex(), bulk[offset + 15:offset + 31].hex())
                print('  span ids tail', [(span.ObjectId, span.IsPrimary, span.PayloadOffset, span.EndOffset) for span in spans[-4:]])


if __name__ == '__main__':
    main()
