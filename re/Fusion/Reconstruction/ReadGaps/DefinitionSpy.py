import collections
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from PackageSpy import ROOT, ReadBundle, packages

from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.formats.Fusion.MaterialCodec.Package.Envelope.ReadLinks import ReadLinks
from convert.formats.Fusion.MaterialCodec.Package.Envelope.ReadResources import ReadResources
from convert.formats.Fusion.MaterialCodec.Package.Schema.ReadSchemaNode import ReadSchemaNode
from convert.formats.Fusion.MaterialCodec.Package.SchemaModels import SchemaModels
from convert.formats.Fusion.MaterialCodec.Records.DecodeAsset import DecodeAsset
from convert.formats.Fusion.MaterialCodec.Schema.BuildSchemas import BuildSchemas
from convert.formats.Fusion.MaterialCodec.Stores.DecodeStore import DecodeStore
from convert.formats.Fusion.MaterialCodec.Table.DecodeTable import DecodeTable


def short(entry):
    return f"{entry.FieldName}={str(getattr(entry, 'Value', entry))[:60]}"


def main():
    model = ReadBundle((ROOT / sys.argv[1]).read_bytes())
    entry = model.Documents[int(sys.argv[2])]
    for _, _, payload in packages(entry.DataValue):
        with OpenFusionZip(payload) as archive:
            prefix = ReadLinks(archive.ReadMember('cnx.xml', 1 << 20))[0] + '/'
            links = ReadResources(archive.ReadMember(prefix + 'Schemas/cnx.xml', 1 << 20))
            schemas = tuple(ReadSchemaNode(archive.ReadMember(prefix + 'Schemas/' + link.FileName, 1 << 20)) for link in links)
            data = prefix + 'AssetData/'
            table = archive.ReadMember(data + 'AssetTableOfContents.bin', 1 << 24)
            defs = archive.ReadMember(data + 'DefinitionIteratorProperties.bin', 1 << 24)
            insts = archive.ReadMember(data + 'InstanceProperties.bin', 1 << 24)
        resolved = BuildSchemas(SchemaModels(schemas))
        entries = DecodeTable(table)
        definitions = DecodeStore(defs, tuple(item.DefinitionRoot for item in entries))
        instances = DecodeStore(insts, tuple(item.InstanceRoot for item in entries))
        assets = [DecodeAsset(*row, resolved) for row in zip(entries, definitions, instances)]
        groups = collections.defaultdict(list)
        for item, asset in zip(entries, assets):
            groups[asset.DefinitionId].append((item, asset))
            print(asset.SchemaName, asset.AssetRole, 'defroot', item.DefinitionRoot, 'defs', len(asset.Definitions), 'props', len(asset.Properties))
        for key, rows in groups.items():
            if len(rows) < 2:
                continue
            print('shared definition', len(rows), 'schemas', {asset.SchemaName for _, asset in rows})
            base = {short(value) for value in rows[0][1].Definitions}
            for _, asset in rows[1:]:
                other = {short(value) for value in asset.Definitions}
                print('   only first', sorted(base - other)[:6])
                print('   only other', sorted(other - base)[:6])


if __name__ == '__main__':
    main()
