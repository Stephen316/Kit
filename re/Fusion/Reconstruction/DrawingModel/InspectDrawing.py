import collections
import hashlib
import io
import json
import struct
from pathlib import Path
import zipfile


BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
CONTENTS = Path('~/Library/Application Support/Autodesk/webdeploy/production/b43a07003c01dd54425db484d23b1c5e6248a21d/Autodesk Fusion.app/Contents').expanduser()
RESOURCES = CONTENTS / 'Resources/CloudWorkFlowsData'


def digest(data):
    return hashlib.sha256(data).hexdigest()


class Reader:
    def __init__(self, data):
        self.data = data
        self.offset = 0
        self.fields = []

    def take(self, count):
        if count < 0 or self.offset + count > len(self.data):
            raise ValueError((self.offset, count, len(self.data)))
        value = self.data[self.offset:self.offset + count]
        self.offset += count
        return value

    def number(self, code):
        return struct.unpack('<' + code, self.take(struct.calcsize('<' + code)))[0]

    def text(self, wide=False):
        count = self.number('I')
        return self.take(count * (2 if wide else 1)).decode('utf-16le' if wide else 'ascii')

    def field(self, name, kind, read):
        start = self.offset
        value = read()
        self.fields.append(dict(name=name, kind=kind, offset=start, length=self.offset - start, value=value))
        return value

    def num(self, name, code='I'):
        return self.field(name, code, lambda: self.number(code))

    def txt(self, name, wide=False):
        return self.field(name, 'utf16' if wide else 'ascii', lambda: self.text(wide))

    def end(self):
        if self.offset != len(self.data):
            raise ValueError(('remaining', self.offset, len(self.data)))


def root_manifest(data):
    r = Reader(data)
    r.txt('format'); r.txt('documentType'); r.txt('extension', True)
    r.txt('typeName', True); r.txt('typeDescription', True)
    r.txt('documentId', True); r.txt('documentCurrentVersion', True)
    r.num('legacySoftwareVersion'); r.num('manifestVersion')
    for index in range(r.num('migratorCount')):
        r.txt(f'migrators[{index}].module'); r.num(f'migrators[{index}].version')
    for index in range(r.num('versionGuidCount')):
        r.txt(f'versionGuids[{index}]', True)
    r.num('referenceHeaderByte', 'B')
    for index in range(r.num('referenceCount')):
        for key in ['role', 'unresolvedText', 'sourcePath', 'targetPath', 'localTargetPath']:
            r.txt(f'references[{index}].{key}', True)
        for number in range(4):
            r.num(f'references[{index}].unresolvedWord{number}')
        for number in range(r.num(f'references[{index}].propertyCount')):
            r.txt(f'references[{index}].properties[{number}].key', True)
            r.txt(f'references[{index}].properties[{number}].value', True)
    r.txt('activeAssetId', True)
    for index in range(r.num('assetCount')):
        r.txt(f'assets[{index}].name', True)
        r.num(f'assets[{index}].unresolvedWord')
        r.num(f'assets[{index}].unresolvedByte', 'B')
    r.txt('documentName', True)
    r.end()
    return r.fields


def asset_manifest(data):
    r = Reader(data)
    for name in ['assetName', 'assetId', 'revisionId']:
        r.txt(name, True)
    r.txt('assetType'); r.num('manifestVersion')
    for index in range(r.num('migratorCount')):
        r.txt(f'migrators[{index}].module'); r.num(f'migrators[{index}].version')
    r.txt('assetKind'); r.num('propertyHeaderByte', 'B')
    for index in range(r.num('linkedAssetCount')):
        for name in ['role', 'linkedAssetId', 'linkRevisionToken']:
            r.txt(f'linkedAssets[{index}].{name}', True)
    r.num('unresolvedSegmentHeaderWord'); r.num('nextSegmentId')
    for index in range(r.num('segmentCount')):
        r.num(f'segments[{index}].id')
        r.txt(f'segments[{index}].userName'); r.txt(f'segments[{index}].type')
    r.end()
    return r.fields


def metadata(data, names):
    r = Reader(data)
    r.txt('userName'); r.num('segmentId'); r.txt('currentVersion', True)
    r.num('legacySoftwareVersion'); r.num('metadataVersion')
    r.txt('segmentType'); r.txt('addIn'); r.num('neutronType')
    for index in range(r.num('ancestryCount')):
        r.txt(f'ancestry[{index}]', True)
    classes = []
    for code in range(256, 256 + r.num('classCount')):
        row = dict(code=code, identifier=r.text(), baseIdentifier=r.text(), schemaVersion=r.number('I'), addIn=r.text())
        row['identities'] = [r.number('Q') for _ in range(r.number('I'))]
        row['name'] = names.get(row['identifier'].upper())
        classes.append(row)
    roots = [r.number('Q') for _ in range(r.num('rootCount'))]
    indexes = {}
    for kind in ['primary', 'continuation']:
        indexes[kind] = [dict(identity=r.number('Q'), offset=r.number('Q')) for _ in range(r.num(kind + 'Count'))]
    r.num('nextEntityId', 'Q'); r.end()
    return dict(header=r.fields, classes=classes, roots=roots, indexes=indexes)


def records(data, meta):
    entries = [dict(entry, primary=kind == 'primary') for kind, values in meta['indexes'].items() for entry in values]
    entries.sort(key=lambda row: row['offset'])
    result = []
    classes = {row['code']: row for row in meta['classes']}
    for index, entry in enumerate(entries):
        end = entries[index + 1]['offset'] if index + 1 < len(entries) else len(data)
        r = Reader(data[entry['offset']:end])
        code = int(r.text()); identity = r.number('Q')
        if identity != entry['identity']:
            raise ValueError('Index identity mismatch')
        row = dict(entry, length=end - entry['offset'], code=code, name=classes[code]['name'], payloadLength=len(r.data) - r.offset)
        row['rootId'] = r.txt('rootId')
        row['entityFrameByte0'] = r.num('entityFrameByte0', 'B')
        row['entityFrameByte1'] = r.num('entityFrameByte1', 'B')
        if identity == 22:
            r.txt('persistedFileName', True); r.end()
        elif identity == 23:
            r.txt('componentFilter', True)
            r.num('rTrackedEntitys.present', 'B'); r.num('rTrackedEntitys.id', 'Q')
            r.num('rTrackedEntitys.segmentQualifier', 'B'); r.num('rTrackedEntitys.assetQualifier', 'B'); r.end()
        elif identity == 25 and entry['primary']:
            r.num('FusionDocAngularDimensionPrecision', 'i')
            for name in ['FusionDocAnnotationFormat', 'FusionDocAnnotationHeight', 'FusionDocDefaultSheetSize', 'FusionDocDrawingUnits', 'FusionDocFont']:
                r.txt(name, True)
            r.num('FusionDocLinearDimensionPrecision', 'i'); r.txt('FusionDocTitleBlock', True)
            r.num('FusionDocUnitDisplay', 'B')
            r.txt('FusionDocViewProjectionDir', True); r.end()
        row['partialFields'] = r.fields
        row['unresolvedBytes'] = len(r.data) - r.offset
        result.append(row)
    return result


def main():
    schema = json.loads((ROOT / 're/Fusion/LocalOracle/Reflection/Schema.json').read_text())
    names = {row['identifier'].upper(): row['name'] for row in schema['metatypes']}
    installed = sorted(RESOURCES.glob('*Boxes Drawing*.f3z'))
    sources = [dict(path=str(path.relative_to(CONTENTS)), bytes=path.stat().st_size, sha256=digest(path.read_bytes())) for path in installed]
    archive = zipfile.ZipFile(installed[0])
    f2d_name = next(name for name in archive.namelist() if name.endswith('.f2d'))
    f2d_data = archive.read(f2d_name)
    drawing = zipfile.ZipFile(io.BytesIO(f2d_data))
    meta_name = 'Documentation[Active]/Design1/MetaStream.dat'
    meta = metadata(drawing.read(meta_name), names)
    versions = {row['identifier'].upper(): row['version'] for row in schema['metatypes']}
    for row in meta['classes']:
        row['currentRegisteredVersion'] = versions.get(row['identifier'].upper())
    inventory = [dict(name=entry.filename, method=entry.compress_type, bytes=entry.file_size, compressedBytes=entry.compress_size, crc32=entry.CRC, sha256=digest(drawing.read(entry))) for entry in drawing.infolist()]
    description = json.loads(archive.read('DesignDescription.json'))
    result = dict(scope='Read-only analysis of public installation resources; no user cloud inventory, no native calls, no test execution', installationResources=sources, uniqueBundleCount=len({row['sha256'] for row in sources}), f2dMember=f2d_name, f2dSha256=digest(f2d_data), f2dBytes=len(f2d_data), members=inventory, rootManifest=root_manifest(drawing.read('Manifest.dat')), assetManifest=asset_manifest(drawing.read('Documentation[Active]/Manifest.dat')), metadata=meta, records=records(drawing.read('Documentation[Active]/Design1/BulkStream.dat'), meta), redirections=json.loads(drawing.read('RedirectionsStream.dat')), bundleManifest=json.loads(archive.read('Manifest.json')), bundleDescription=description)
    dwg = drawing.read(next(name for name in drawing.namelist() if name.lower().endswith('.dwg')))
    result['dwg'] = dict(signature=dwg[:6].decode('ascii'), bytes=len(dwg), sha256=digest(dwg), decodedSemantics=False)
    result['dependentModelContainers'] = []
    for name in archive.namelist():
        if not name.endswith('.f3d'):
            continue
        payload = archive.read(name)
        model = zipfile.ZipFile(io.BytesIO(payload))
        segments = []
        for member in model.namelist():
            if member.endswith('/MetaStream.dat'):
                value = metadata(model.read(member), names)
                segments.append(dict(member=member, header=value['header'], classCount=len(value['classes']), primaryCount=len(value['indexes']['primary']), continuationCount=len(value['indexes']['continuation'])))
        asset = Reader(model.read('FusionAssetName[Active]/Manifest.dat'))
        asset_header = dict(name=asset.text(True), assetId=asset.text(True), revisionId=asset.text(True))
        result['dependentModelContainers'].append(dict(member=name, sha256=digest(payload), assetHeader=asset_header, members=[dict(name=entry.filename, method=entry.compress_type, bytes=entry.file_size) for entry in model.infolist()], segments=segments))
    local = collections.Counter()
    for folder in ['re', 'examples']:
        for path in (ROOT / folder).rglob('*'):
            if path.is_file() and path.suffix.lower() in {'.f3d', '.f3z', '.f2d', '.f2z', '.f2t', '.f3t'}:
                local[path.suffix.lower()] += 1
    result['localFileExtensionCounts'] = dict(local)
    result['localCountScope'] = 'All filenames under re/ and examples/, including generated controls; filenames only, no private bundle inventory content read; counts can increase during ongoing authoring'
    result['drawingMetatypeCatalog'] = [dict(name=row['name'], identifier=row['identifier'], baseIdentifier=row['base_identifier'], version=row['version'], category=row['category']) for row in schema['metatypes'] if row['addin'] == 'FusionDoc']
    (BASE / 'DrawingInventory.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(f2dBytes=len(f2d_data), classCount=len(meta['classes']), recordCount=len(result['records']), localFileExtensionCounts=dict(local), dwg=result['dwg']), indent=2))


if __name__ == '__main__':
    main()
