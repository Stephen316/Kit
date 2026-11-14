import collections
import dataclasses
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.setrecursionlimit(20000)

from CacheSpy import ROOT

from convert.formats.Fusion.BundleCodec.ReadBundle import ReadBundle
import convert.formats.Fusion.DocumentCodec.ReadDocument as Reader
from convert.formats.Fusion.GraphicsCodec.Model.Values.EntityRef import EntityRef


KINDS = collections.Counter()


def walk(value, trail, found):
    KINDS[type(value).__name__] += 1
    if type(value).__name__ == 'NodeTarget':
        KINDS['NodeTarget external' if value.ExternalRef else 'NodeTarget node'] += 1
    if type(value).__name__ == 'OverrideSet':
        KINDS['OverrideSet children'] += len(value.ChildSets)
    if isinstance(value, EntityRef):
        found.append((trail, value))
    elif isinstance(value, tuple):
        for item in value:
            walk(item, trail, found)
    elif dataclasses.is_dataclass(value) and not isinstance(value, type):
        for field in dataclasses.fields(value):
            walk(getattr(value, field.name), trail + (type(value).__name__ + '.' + field.name,), found)


def main():
    Reader.CheckDocLinks = lambda value: None
    Reader.CheckDocScene = lambda value: None
    member = int(sys.argv[1])
    data = ReadBundle((ROOT / 're/Fusion/examples/.f3z/example1.f3z').read_bytes()).Documents[member].DataValue
    model = Reader.ReadDocument(data)
    owners = {(segment.Metadata.Header.SegmentId, record.ObjectId) for segment in model.Segments for record in segment.Records if record.IsPrimary}
    segments = sorted({segment.Metadata.Header.SegmentId for segment in model.Segments})
    found = []
    walk(model.Graphics, (), found)
    counts = collections.Counter()
    for trail, value in found:
        key = ' > '.join(item for item in trail[-2:])
        counts[(key, (value.SegmentId, value.ObjectId) in owners, value.SegmentId)] += 1
    print('segments', segments)
    for key, count in sorted(counts.items()):
        print(count, key)
    print({key: KINDS[key] for key in sorted(KINDS) if key.startswith(('Node', 'Override', 'PathEntity', 'GraphicAttr'))})


if __name__ == '__main__':
    main()
