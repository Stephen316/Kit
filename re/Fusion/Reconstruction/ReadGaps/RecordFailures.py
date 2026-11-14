import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE))

from ExampleRecords import documents
from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.Records.MakeDocProfile import MakeDocProfile
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.formats.Fusion.EntityCodec.Records.BindRecords import BindRecords
from convert.formats.Fusion.EntityCodec.Records.ReadEntity import ReadSlack
from convert.formats.Fusion.EntityCodec.Schema.BindProfile import BindProfile
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire

GAPS = json.loads((BASE.parent / 'ReaderCoverage' / 'ExampleGaps.json').read_text())['gaps']
NAMES = {gap['class_guid'].upper(): gap['class'].split('::')[-1] for gap in GAPS}


def label(guid):
    return NAMES.get(guid.upper(), guid[:8])


def failures(data):
    container = ReadContainer(data)
    schemas = ReadDocSchemas()
    metas = tuple(ReadMetaWire(stream.Metadata, Segment=slot.Segment) for stream, slot in zip(container.Streams, container.Asset.Segments, strict=True))
    found = collections.Counter()
    for stream, meta in zip(container.Streams, metas, strict=True):
        try:
            profile = MakeDocProfile(schemas, metas, stream.SegmentId)
            catalog = BindProfile(profile, meta.Classes)
        except Exception as error:
            found[(meta.Header.Segment.name, 'profile', str(error)[:70])] += 1
            continue
        spans = list(ReadBulkSpans(stream.BulkData, stream.Metadata, Segment=meta.Header.Segment))
        items = tuple(BulkRecord(span.TypeCode, span.ObjectId, span.IsPrimary, stream.BulkData[span.PayloadOffset:span.EndOffset]) for span in spans)
        scope = BindRecords(items, meta.Classes)
        versions = {row.ClassGuid.upper(): row.SchemaVersion for row in meta.Classes}
        for index, (span, item) in enumerate(zip(spans, items)):
            try:
                value, slack = ReadSlack(item, scope, catalog)
                if slack:
                    found[(meta.Header.Segment.name, f'{label(span.ClassGuid)}{versions.get(span.ClassGuid.upper())}', f'slack {len(slack)}')] += 1
            except Exception as error:
                found[(meta.Header.Segment.name, f'{label(span.ClassGuid)}{versions.get(span.ClassGuid.upper())}', str(error)[:70])] += 1
    return found


def main():
    for name, data in documents():
        found = failures(data)
        print(name[-30:], sum(found.values()))
        for key, count in sorted(found.items()):
            print('   ', count, *key)


if __name__ == '__main__':
    main()
