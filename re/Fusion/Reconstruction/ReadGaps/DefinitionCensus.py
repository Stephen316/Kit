import collections
import io
import json
import sys
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE))

from Sweep import tracked


def designs(name):
    data = (ROOT / name).read_bytes()
    if name.lower().endswith('.f3z'):
        with zipfile.ZipFile(io.BytesIO(data)) as outer:
            for index, info in enumerate(outer.infolist()):
                if info.filename.lower().endswith('.f3d'):
                    yield name, outer.read(info)
    elif name.lower().endswith('.f3d'):
        yield name, data


def packages(data):
    try:
        outer = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        return
    with outer:
        for info in outer.infolist():
            payload = outer.read(info)
            if payload.startswith(b'PK'):
                try:
                    inner = zipfile.ZipFile(io.BytesIO(payload))
                except zipfile.BadZipFile:
                    continue
                if 'cnx.xml' in inner.namelist():
                    yield inner


def assets(inner):
    from convert.formats.Fusion.MaterialCodec.Package.Envelope.ReadLinks import ReadLinks
    from convert.formats.Fusion.MaterialCodec.Package.Envelope.ReadResources import ReadResources
    from convert.formats.Fusion.MaterialCodec.Package.Schema.ReadSchemaNode import ReadSchemaNode
    from convert.formats.Fusion.MaterialCodec.Package.SchemaModels import SchemaModels
    from convert.formats.Fusion.MaterialCodec.Records.DecodeAsset import DecodeAsset
    from convert.formats.Fusion.MaterialCodec.Schema.BuildSchemas import BuildSchemas
    from convert.formats.Fusion.MaterialCodec.Stores.DecodeStore import DecodeStore
    from convert.formats.Fusion.MaterialCodec.Table.DecodeTable import DecodeTable
    prefix = ReadLinks(inner.read('cnx.xml'))[0] + '/'
    folders = ReadLinks(inner.read(prefix + 'cnx.xml'))
    links = ReadResources(inner.read(prefix + 'Schemas/cnx.xml'))
    schemas = tuple(ReadSchemaNode(inner.read(prefix + 'Schemas/' + link.FileName)) for link in links)
    data = prefix + 'AssetData/'
    entries = DecodeTable(inner.read(data + 'AssetTableOfContents.bin'))
    defs = DecodeStore(inner.read(data + 'DefinitionIteratorProperties.bin'), tuple(item.DefinitionRoot for item in entries))
    insts = DecodeStore(inner.read(data + 'InstanceProperties.bin'), tuple(item.InstanceRoot for item in entries))
    resolved = BuildSchemas(SchemaModels(schemas))
    return folders, [DecodeAsset(*row, resolved) for row in zip(entries, defs, insts)]


def scan(name):
    result = {'packages': 0, 'assets': 0, 'shared': 0, 'differ': 0, 'fields': collections.Counter(), 'files': [], 'folders': collections.Counter(), 'errors': 0}
    try:
        for label, data in designs(name):
            for inner in packages(data):
                try:
                    folders, found = assets(inner)
                except Exception:
                    result['errors'] += 1
                    continue
                result['packages'] += 1
                result['assets'] += len(found)
                result['folders'][','.join(folders)] += 1
                groups = collections.defaultdict(list)
                for asset in found:
                    groups[asset.DefinitionId].append(asset)
                for rows in groups.values():
                    if len(rows) < 2:
                        continue
                    result['shared'] += 1
                    tables = [{entry.FieldName: repr(entry) for entry in asset.Definitions} for asset in rows]
                    schemas = {asset.SchemaName for asset in rows}
                    keys = set().union(*tables)
                    differ = sorted(key for key in keys if len({table.get(key) for table in tables}) > 1)
                    if differ or len(schemas) > 1:
                        result['differ'] += 1
                        result['fields'][','.join(differ) + (' +schema' if len(schemas) > 1 else '')] += 1
                        if label not in result['files']:
                            result['files'].append(label)
    except Exception:
        result['errors'] += 1
    return result


def main():
    names = [name for name in tracked() if not name.lower().endswith('.f2d')]
    total = {'packages': 0, 'assets': 0, 'shared': 0, 'differ': 0, 'errors': 0}
    fields, folders, files = collections.Counter(), collections.Counter(), []
    with ProcessPoolExecutor(8) as pool:
        for result in pool.map(scan, names, chunksize=8):
            for key in total:
                total[key] += result[key]
            fields.update(result['fields'])
            folders.update(result['folders'])
            files.extend(result['files'])
    report = {'files': len(names), **total, 'fields': dict(fields), 'folders': dict(folders), 'differing': files}
    (BASE / 'DefinitionCensus.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({key: report[key] for key in ('files', 'packages', 'assets', 'shared', 'differ', 'errors', 'folders', 'fields')}))
    for name in files[:10]:
        print(name)


if __name__ == '__main__':
    main()
