import collections
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from PackageSpy import ROOT, ReadBundle, packages

from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.formats.Fusion.MaterialCodec.Package.Envelope.ReadLinks import ReadLinks
from convert.formats.Fusion.MaterialCodec.Package.Reading.ReadPackageBody import ReadPackageBody
from convert.formats.Fusion.MaterialCodec.Package.Validation.CheckPackage import CheckPackage


def walk(value, path, found, depth=0):
    if depth > 12:
        return
    if isinstance(value, str):
        if any(token in value.lower() for token in ('thumb', 'png', 'resource')) or len(value) == 36 or value.endswith('_Post2015'):
            found[path].add(value[:80])
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            walk(item, path, found, depth + 1)
        return
    slots = getattr(value, '__slots__', None) or getattr(value, '__dataclass_fields__', None)
    if slots:
        for name in slots:
            walk(getattr(value, name, None), path + '.' + name, found, depth + 1)


def main():
    model = ReadBundle((ROOT / sys.argv[1]).read_bytes())
    entry = model.Documents[int(sys.argv[2])]
    for _, _, payload in packages(entry.DataValue):
        with OpenFusionZip(payload) as archive:
            prefix = ReadLinks(archive.ReadMember('cnx.xml', 1 << 20))[0] + '/'
            print('asset links', ReadLinks(archive.ReadMember(prefix + 'cnx.xml', 1 << 20)))
            result = ReadPackageBody(archive, prefix, True)
            CheckPackage(result)
            unread = sorted(set(archive.Entries) - archive.ReadNames)
            print('assets', len(result.Assets), 'unread', len(unread))
            print('unread tops', collections.Counter('/'.join(name.split('/')[:2]) for name in unread))
            print('resource folders', sorted({name.split('/')[2] for name in unread if name.count('/') >= 3}))
            for asset in result.Assets:
                found = collections.defaultdict(set)
                walk(asset, 'asset', found)
                for key, values in found.items():
                    print('  ', key[:90], sorted(values)[:4])


if __name__ == '__main__':
    main()
