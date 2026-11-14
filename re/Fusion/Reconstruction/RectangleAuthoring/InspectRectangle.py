import collections
import hashlib
import json
import lzma
import runpy
import sys
from pathlib import Path


sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
API = runpy.run_path(str(BASE.parent / 'EntityGraph/DecodeGraph.py'))
SOURCE = ROOT / 're/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d'


def main():
    archive = API['TOOLS']['read_archive'](SOURCE)
    codec = API['GraphCodec'](archive)
    continuations = collections.defaultdict(set)
    for record in archive['records']:
        if not record['primary']:
            continuations[record['identity']].add(record['class']['identifier'].upper())
    decoded = []
    for record in archive['records']:
        identifier = record['class']['identifier'].upper()
        reader = API['TOOLS']['Reader'](record['payload'])
        stops = continuations[record['identity']] - ({identifier} if not record['primary'] else set())
        frame = codec.read_frame(reader, record['primary'])
        groups = codec.read_groups(reader, codec.groups(identifier, stops))
        if reader.offset != len(reader.data):
            raise ValueError('Unexplained rectangle record bytes: ' + str(record['identity']))
        decoded.append({
            'entityId': record['identity'], 'primary': record['primary'],
            'className': codec.schema[identifier]['name'], 'classId': identifier,
            'payloadBytes': len(record['payload']), 'frame': frame, 'groups': groups,
        })
    report = {
        'schema': 'FusionRectangleDesignResearch/1',
        'scope': 'Read-only saved archive decoding with research schema; no production codec execution, native calls or local tests',
        'source': str(SOURCE.relative_to(ROOT)),
        'sourceSha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'classes': list(archive['classes'].values()), 'records': decoded,
    }
    raw = (json.dumps(report, indent=2, allow_nan=False) + '\n').encode()
    packed = lzma.compress(raw, preset=9)
    (BASE / 'ControlGraph.json.xz').write_bytes(packed)
    summary = {
        key: value for key, value in report.items() if key not in ('classes', 'records')
    }
    summary.update({
        'recordCount': len(decoded),
        'primaryCount': sum(record['primary'] for record in decoded),
        'classCounts': dict(sorted(collections.Counter(record['className'] for record in decoded if record['primary']).items())),
        'payloadBytes': sum(record['payloadBytes'] for record in decoded),
        'artifact': 'ControlGraph.json.xz',
        'artifactSha256': hashlib.sha256(packed).hexdigest(),
    })
    (BASE / 'ControlSummary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
