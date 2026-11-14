import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))

from convert.adapters.Fusion.Projection.NativeMaterial import NativeMaterial
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.DocumentCodec.Reading.Materials.ReadMatRefs import ReadMatRefs

NAMES = ('physmat_Label', 'UIName', 'BaseSchema', 'description', 'physmat_Type', 'physmat_Class')


def main():
    for name in sys.argv[1:]:
        model = ReadDocument((ROOT / name).read_bytes())
        found = ReadMatRefs(model, 'physicalMaterial') or ReadMatRefs(model, 'defaultPhysicalMaterial')
        print(name, 'refs', len(found))
        for package, identity in found:
            if package is None:
                continue
            asset = next(item for item in package.Assets if item.InstanceId == identity)
            print('  schema', asset.SchemaName, 'role', asset.AssetRole)
            for group, entries in (('def', asset.Definitions), ('prop', asset.Properties)):
                for entry in entries:
                    if entry.FieldName in NAMES or 'name' in entry.FieldName.lower() or 'label' in entry.FieldName.lower():
                        print('   ', group, entry.FieldName, repr(entry.Value)[:60])
        spec = NativeMaterial(model)
        print('  spec name', repr(spec.NameValue), 'density', spec.Density, 'finish', repr(spec.Finish.NameValue if spec.Finish else None))


if __name__ == '__main__':
    main()
