import io
import sys
import zipfile
from pathlib import Path


def document_bytes(path, member=None):
    data = Path(path).read_bytes()
    if str(path).endswith('.f3z'):
        with zipfile.ZipFile(io.BytesIO(data)) as outer:
            if member is None:
                import json
                member = json.loads(outer.read('Manifest.json'))['root']
            data = outer.read(member)
    return data


def members(path, member=None):
    data = document_bytes(path, member)
    with zipfile.ZipFile(io.BytesIO(data)) as inner:
        return {name: inner.read(name) for name in inner.namelist()}


if __name__ == '__main__':
    found = members(sys.argv[1], sys.argv[2] if len(sys.argv) > 3 else None)
    target = Path(sys.argv[-1])
    target.mkdir(parents=True, exist_ok=True)
    for name, value in found.items():
        if name.endswith('/'):
            continue
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
