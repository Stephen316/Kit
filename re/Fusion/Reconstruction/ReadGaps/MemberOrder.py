import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.BundleCodec.ReadBundle import ReadBundle


def main():
    data = (ROOT / 're/Fusion/examples/.f3z/example1.f3z').read_bytes()
    bundle = {hashlib.sha256(entry.DataValue).hexdigest(): index for index, entry in enumerate(ReadBundle(data).Documents)}
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = sorted(archive.namelist())
        print('sorted index -> bundle member', {index: bundle.get(hashlib.sha256(archive.read(name)).hexdigest()) for index, name in enumerate(names) if name.endswith('.f3d')})
    label = sys.argv[1] if len(sys.argv) > 1 else 'width'
    rows = json.loads((BASE / f'Sweep-{label}.json').read_text())['rows']
    row = next(item for item in rows if item['file'].endswith('examples/.f3z/example1.f3z'))
    print([(member['member'], member['read'], member.get('message', '')[:40]) for member in row['members'] if member['suffix'] == '.f3d'])


if __name__ == '__main__':
    main()
