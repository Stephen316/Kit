import collections
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from PackageSpy import ROOT, ReadBundle

from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.DocumentCodec.Reading.Materials.ReadMatRefs import ReadMatRefs


def main():
    model = ReadBundle((ROOT / sys.argv[1]).read_bytes())
    document = ReadDocument(model.Documents[int(sys.argv[2])].DataValue)
    print('bodies', len(document.Bodies), 'packages', len(document.Materials))
    for field in ('physicalMaterial', 'defaultPhysicalMaterial', 'visualMaterial', 'defaultVisualMaterial'):
        found = ReadMatRefs(document, field)
        kinds = collections.Counter(asset.SchemaName for package, identity in found if package is not None for asset in package.Assets if asset.InstanceId == identity)
        print(field, len(found), 'empty', sum(package is None for package, _ in found), dict(kinds))


if __name__ == '__main__':
    main()
