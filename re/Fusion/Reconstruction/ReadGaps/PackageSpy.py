import io
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.BundleCodec.ReadBundle import ReadBundle


def packages(data):
    with zipfile.ZipFile(io.BytesIO(data)) as outer:
        for info in outer.infolist():
            payload = outer.read(info)
            if not payload.startswith(b'PK'):
                continue
            try:
                inner = zipfile.ZipFile(io.BytesIO(payload))
            except zipfile.BadZipFile:
                continue
            if 'cnx.xml' in inner.namelist():
                yield info.filename, inner, payload


def main():
    model = ReadBundle((ROOT / sys.argv[1]).read_bytes())
    entry = model.Documents[int(sys.argv[2])]
    for name, inner, _ in packages(entry.DataValue):
        names = inner.namelist()
        print(name.rsplit('/', 1)[-1][:40], len(names))
        for member in names:
            if member.endswith('cnx.xml') and member.count('/') == 1:
                text = inner.read(member).decode('utf-8', 'replace')
                print('  ', member.split('/')[1], [part.split('"')[0] for part in text.split('name="')[1:]])
        folders = sorted({member.split('/')[1] for member in names if member.count('/') >= 2})
        print('   folders', folders)


if __name__ == '__main__':
    main()
