import collections
import hashlib
import json
import runpy
import sys
from pathlib import Path
from zipfile import ZipFile

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
API = runpy.run_path(str(BASE.parent / 'EntityGraph/DecodeGraph.py'))
SOURCES = [
    'RectangleAuthoring/Initial/ProductionCuboid.f3d',
    'RectangleAuthoring/mass_probe_ProductionCuboid.f3d',
    'RectangleAuthoring/vendor_ProductionRectangle37mm.f3d',
]


def inspect(path, codec=None):
    archive = API['TOOLS']['read_archive'](path)
    if codec is None:
        codec = API['GraphCodec'](archive)
    codec.classes = {item['identifier'].upper(): item for item in archive['classes'].values()}
    continuations = collections.defaultdict(set)
    for record in archive['records']:
        if not record['primary']:
            continuations[record['identity']].add(record['class']['identifier'].upper())
    decoded = []
    for record in archive['records']:
        identity = record['class']['identifier'].upper()
        name = codec.schema[identity]['name']
        if name not in ('Body', 'BodyMetaType', 'ProteinAssetManager', 'ProteinAssetManagerMetaType', 'Component', 'ComponentMetaType'):
            continue
        reader = API['TOOLS']['Reader'](record['payload'])
        stops = continuations[record['identity']] - ({identity} if not record['primary'] else set())
        frame = codec.read_frame(reader, record['primary'])
        groups = codec.read_groups(reader, codec.groups(identity, stops))
        if reader.offset != len(reader.data):
            raise ValueError('Unexplained record bytes')
        decoded.append({'entityId': record['identity'], 'className': name, 'primary': record['primary'], 'frame': frame, 'groups': groups})
    with ZipFile(path) as archive_file:
        entries = [{'name': item.filename, 'bytes': item.file_size} for item in archive_file.infolist() if 'protein' in item.filename.lower()]
    return {'source': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'materials': entries, 'records': decoded}, codec


def main():
    result = []
    codec = None
    for name in SOURCES:
        entry, codec = inspect(ROOT / 're/Fusion/LocalOracle' / name, codec)
        result.append(entry)
    target = BASE / 'MassFields.json'
    target.write_text(json.dumps({'scope': 'Read-only material assignment field comparison with research decoder; no production execution', 'cases': result}, indent=2) + '\n')
    print(json.dumps({'path': str(target), 'records': [len(item['records']) for item in result]}))


if __name__ == '__main__':
    main()
