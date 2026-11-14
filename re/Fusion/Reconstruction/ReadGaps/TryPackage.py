import io
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.setrecursionlimit(20000)

from convert.formats.Fusion.BundleCodec.ReadBundle import ReadBundle
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.MaterialCodec.Package.EmitPackage import EmitPackage
from convert.formats.Fusion.MaterialCodec.Package.ReadPackage import ReadPackage

FIELD = re.compile(rb'<(\w+) name="([^"]*)">([^<]*)<')


def fields(payload):
    return sorted(FIELD.findall(payload))


def main():
    model = ReadBundle((ROOT / sys.argv[1]).read_bytes())
    entry = model.Documents[int(sys.argv[2])]
    with zipfile.ZipFile(io.BytesIO(entry.DataValue)) as outer:
        for info in outer.infolist():
            if not info.filename.endswith('.protein'):
                continue
            source = outer.read(info)
            package = ReadPackage(source)
            if package.Resources is None:
                continue
            written = EmitPackage(package)
            print('package model round trip', ReadPackage(written) == package)
            with zipfile.ZipFile(io.BytesIO(source)) as first, zipfile.ZipFile(io.BytesIO(written)) as second:
                old = set(first.namelist())
                new = set(second.namelist())
                print('members', len(old), len(new), 'same names', old == new)
                same = differ = equal = 0
                for name in sorted(old & new):
                    left = first.read(name)
                    right = second.read(name)
                    if left == right:
                        same += 1
                    elif name.endswith('.xml') and fields(left) == fields(right):
                        equal += 1
                    else:
                        differ += 1
                        print('  differs', name.split('/', 1)[-1][-60:])
                print('byte equal', same, 'field equal', equal, 'different', differ)
    document = ReadDocument(entry.DataValue)
    again = ReadDocument(EmitParsed(document))
    print('document model round trip', again == document)


if __name__ == '__main__':
    main()
