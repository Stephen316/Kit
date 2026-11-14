import collections
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.setrecursionlimit(20000)

from CacheSpy import ROOT

from convert.formats.Fusion.BundleCodec.ReadBundle import ReadBundle
import convert.formats.Fusion.DocumentCodec.ReadDocument as Reader
from convert.formats.Fusion.DocumentCodec.Auxiliary.Graphics.CheckDocScene import CheckDocScene
from convert.formats.Fusion.SegmentCodec.Manifest.LinkLayout import KLinkedUrl

VERSION = re.compile(r'version=(\d+)')


def version(text):
    if text is None:
        return None
    match = VERSION.search(text)
    return int(match.group(1)) if match else 'other'


def stem(text):
    return (text or '').split('?')[0]


def main():
    Reader.CheckDocLinks = lambda value: None
    bundle = sys.argv[1]
    member = int(sys.argv[2])
    data = ReadBundle((ROOT / bundle).read_bytes()).Documents[member].DataValue
    model = Reader.ReadDocument(data)
    CheckDocScene(model)
    print('scene check passes')
    urls = {entry.LinkId: dict(entry.Properties).get(KLinkedUrl) for entry in model.Document.Links}
    assets = {entry.LinkId: entry.AssetId for entry in model.Asset.Links}
    shapes = collections.Counter()
    for segment in model.Segments:
        for context in segment.Metadata.Contexts:
            link = urls.get(context.LinkId)
            shapes[(
                assets.get(context.LinkId) == context.AssetId,
                stem(link) == stem(context.VersionUrn),
                version(link),
                version(context.VersionUrn),
            )] += 1
    print('links', len(urls), 'contexts (asset equal, urn stem equal, link version, context version)')
    for key, count in sorted(shapes.items(), key=str):
        print(' ', count, key)


if __name__ == '__main__':
    main()
