import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
BUNDLES = ('re/Fusion/examples/.f3z/example1.f3z', 're/Fusion/LocalOracle/Bundles/kit_production_example1.f3z')


def digest(data):
    return hashlib.sha256(data).hexdigest()[:16]


def inner(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        rows = archive.infolist()
        return {
            'members': len(rows),
            'methods': sorted({row.compress_type for row in rows}),
            'times': sorted({row.date_time for row in rows})[:2],
            'scene': {row.filename.rsplit('/', 1)[1]: digest(archive.read(row.filename)) for row in rows if 'DefaultScene/' in row.filename and not row.filename.endswith('/')},
        }


def outer(name):
    with zipfile.ZipFile(ROOT / name) as archive:
        rows = archive.infolist()
        return {
            'order': [row.filename[:8] for row in rows],
            'methods': sorted({row.compress_type for row in rows}),
            'times': sorted({row.date_time for row in rows})[:2],
            'documents': {row.filename[:8]: {'sha': digest(archive.read(row.filename))} | (inner(archive.read(row.filename)) if row.filename.endswith('.f3d') else {}) for row in rows},
        }


if __name__ == '__main__':
    found = {name: outer(name) for name in BUNDLES}
    first, second = (found[name] for name in BUNDLES)
    report = {
        'outer': {name: {key: value for key, value in found[name].items() if key != 'documents'} for name in BUNDLES},
        'same_document_bytes': sorted(key for key in first['documents'] if first['documents'][key]['sha'] == second['documents'].get(key, {}).get('sha')),
        'same_scene_members': sorted(key for key in first['documents'] if first['documents'][key].get('scene') and first['documents'][key].get('scene') == second['documents'].get(key, {}).get('scene')),
        'inner': {key: {name: {k: v for k, v in found[name]['documents'][key].items() if k in ('members', 'methods', 'times')} for name in BUNDLES} for key in first['documents']},
    }
    print(json.dumps(report, indent=1, default=str))
