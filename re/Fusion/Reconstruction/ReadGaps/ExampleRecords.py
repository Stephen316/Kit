import hashlib
import io
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire

SOURCES = ('re/Fusion/examples/.f3d/example2.f3d', 're/Fusion/examples/.f3z/example1.f3z')


def documents():
    seen = set()
    for name in SOURCES:
        data = (ROOT / name).read_bytes()
        if name.endswith('.f3z'):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                for index, member in enumerate(sorted(archive.namelist())):
                    if member.endswith('.f3d'):
                        payload = archive.read(member)
                        key = hashlib.sha256(payload).hexdigest()
                        if key not in seen:
                            seen.add(key)
                            yield f'{name} member {index}', payload
        else:
            seen.add(hashlib.sha256(data).hexdigest())
            yield name, data


def segments(data):
    container = ReadContainer(data)
    for stream, slot in zip(container.Streams, container.Asset.Segments, strict=True):
        meta = ReadMetaWire(stream.Metadata, Segment=slot.Segment)
        rows = list(ReadBulkSpans(stream.BulkData, stream.Metadata, Segment=slot.Segment))
        yield slot.Segment.name, meta, rows, stream.BulkData


def records(guid, version=None):
    for name, data in documents():
        for segment, meta, rows, bulk in segments(data):
            versions = {row.ClassGuid.upper(): row.SchemaVersion for row in meta.Classes}
            if guid.upper() not in versions or (version is not None and versions[guid.upper()] != version):
                continue
            for span in rows:
                if span.ClassGuid.upper() == guid.upper():
                    yield name, segment, meta, span, bulk[span.PayloadOffset:span.EndOffset]
