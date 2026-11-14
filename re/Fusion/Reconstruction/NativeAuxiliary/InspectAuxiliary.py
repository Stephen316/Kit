import collections
import hashlib
import json
import lzma
from pathlib import Path
import runpy
from zipfile import ZipFile

root = Path(__file__).resolve().parents[4]
out = Path(__file__).resolve().parent
read = runpy.run_path(str(root / 're/Fusion/Reconstruction/BrepTokens.py'))['read_stream']
paths = (
    're/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d',
    're/Fusion/LocalOracle/RectangleAuthoring/vendor_ProductionCuboid37mm.f3d',
    're/Fusion/LocalOracle/Features/extrude_07mm.f3d',
)
reports = []
snapshots = {}
for relative in paths:
    source = root / relative
    report = {'source': relative, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'members': []}
    with ZipFile(source) as archive:
        for info in archive.infolist():
            payload = archive.read(info)
            entry = {'name': info.filename, 'bytes': len(payload), 'directory': info.is_dir(), 'compression': info.compress_type, 'sha256': hashlib.sha256(payload).hexdigest()}
            if info.filename.endswith(('.dsgcfg', '.dsgcfgrule')):
                entry['json'] = json.loads(payload)
            if info.filename.endswith('.smb'):
                parsed = read(payload)
                snapshots[relative] = parsed
                entry['record_counts'] = dict(collections.Counter(record['name'] for record in parsed['records']))
                entry['header'] = parsed['header']
            report['members'].append(entry)
    reports.append(report)
encoded = json.dumps(snapshots, separators=(',', ':')).encode()
compressed = lzma.compress(encoded)
(out / 'SnapshotTokens.json.xz').write_bytes(compressed)
index = {'sources': reports, 'snapshot_tokens': {'path': 'SnapshotTokens.json.xz', 'sha256': hashlib.sha256(compressed).hexdigest(), 'uncompressed_sha256': hashlib.sha256(encoded).hexdigest(), 'uncompressed_bytes': len(encoded)}, 'scope': 'Research-only raw framing analysis; product models contain no retained tokens or source payloads'}
(out / 'Inventory.json').write_text(json.dumps(index, indent=2) + '\n')
print(json.dumps({'archives': len(reports), 'compressed_snapshot_bytes': len(compressed), 'snapshot_sha256': index['snapshot_tokens']['sha256']}))
