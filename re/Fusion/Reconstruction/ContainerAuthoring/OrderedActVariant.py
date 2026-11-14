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


def main():
    source = BASE / 'StoredFolders' / 'AuthoredParameter.f3d'
    identity = hashlib.sha256(source.read_bytes()).hexdigest()
    if identity != '2bee9d409dbdc8f651a08bb035213d6491edd15da3ddb47068f3e5c1e162b11e':
        raise ValueError('Only the frozen independently authored diagnostic candidate is allowed')
    model = json.loads(lzma.decompress((BASE / 'Generated' / 'ActModel.json.xz').read_bytes()))
    segment = AUTHOR['Segment'](model['kind'], model['segmentId'], 5, {'Application': 1, 'Server': 1})
    segment.records = sorted(model['records'], key=lambda record: (record['identity'], not record['primary']))
    segment.roots = model['roots']
    result = segment.emit()
    destination = BASE / 'OrderedAct'
    destination.mkdir(exist_ok=True)
    output = destination / 'AuthoredParameter.f3d'
    prefix = 'FusionAssetName[Active]/FusionACTSegmentType1/'
    replacements = {prefix + 'MetaStream.dat': result['metadata'], prefix + 'BulkStream.dat': result['bulk']}
    members = []
    with zipfile.ZipFile(source) as archive, zipfile.ZipFile(output, 'w') as generated:
        for original in archive.infolist():
            data = replacements.get(original.filename)
            if data is None:
                data = archive.read(original)
            generated.writestr(copy.copy(original), data)
            members.append({'name': original.filename, 'method': original.compress_type, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    (destination / 'ActModel.json').write_text(json.dumps(result['model'], indent=2) + '\n')
    report = {'purpose': 'ACT physical record order diagnostic with identical authored semantic values and UUIDs', 'sourceCandidateSha256': identity, 'candidate': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'changedMembers': list(replacements), 'beforeOrder': [record['identity'] for record in model['records']], 'afterOrder': [record['identity'] for record in segment.records], 'members': members}
    (destination / 'Generation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
