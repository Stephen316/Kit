import copy
import hashlib
import json
import lzma
import runpy
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
AUTHOR = runpy.run_path(str(BASE / 'AuthorContainer.py'))


def correct(value):
    if isinstance(value, dict):
        if value.get('entityId') == 1034 and value.get('segmentId') == 0:
            value['entityId'] = 1022
        for child in value.values():
            correct(child)
    elif isinstance(value, list):
        for child in value:
            correct(child)


def main():
    source = BASE / 'BrepFolder' / 'AuthoredParameter.f3d'
    identity = hashlib.sha256(source.read_bytes()).hexdigest()
    if identity != 'e2b94c7e74a8206fc0027ed3a830f0c5f8d40f421820b98b524a9d32d77037e4':
        raise ValueError('Only the frozen independently authored diagnostic candidate is allowed')
    model = json.loads(lzma.decompress((BASE / 'Generated' / 'BrowserModel.json.xz').read_bytes()))
    correct(model['records'])
    segment = AUTHOR['Segment'](model['kind'], model['segmentId'], 6, {'Application': 2, 'Server': 2})
    segment.records = model['records']
    segment.roots = model['roots']
    result = segment.emit()
    destination = BASE / 'BrowserBindings'
    destination.mkdir(exist_ok=True)
    output = destination / 'AuthoredParameter.f3d'
    prefix = 'FusionAssetName[Active]/FusionBrowserSegmentType1/'
    replacements = {prefix + 'MetaStream.dat': result['metadata'], prefix + 'BulkStream.dat': result['bulk']}
    members = []
    with zipfile.ZipFile(source) as archive, zipfile.ZipFile(output, 'w') as generated:
        for original in archive.infolist():
            data = replacements.get(original.filename)
            if data is None:
                data = archive.read(original)
            generated.writestr(copy.copy(original), data)
            members.append({'name': original.filename, 'method': original.compress_type, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    (destination / 'BrowserModel.json').write_text(json.dumps(result['model'], indent=2) + '\n')
    report = {'purpose': 'Correct relationship browser reference targets from Relationships to AssyConstraints; preserve all other semantic values and UUIDs', 'sourceCandidateSha256': identity, 'candidate': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'rewrittenMembers': list(replacements), 'oldTarget': {'segmentId': 0, 'entityId': 1034, 'type': 'Relationships'}, 'newTarget': {'segmentId': 0, 'entityId': 1022, 'type': 'AssyConstraints'}, 'members': members}
    (destination / 'Generation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
