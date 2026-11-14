import collections
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE))
sys.setrecursionlimit(20000)


def references(model):
    from convert.formats.Fusion.DocumentCodec.Reading.Materials.BindMaterials import BindMaterials
    from convert.formats.Fusion.DocumentCodec.Reading.Materials.GroupFields import GroupFields
    from convert.formats.Fusion.DocumentCodec.Reading.Materials.ResolveMatAsset import ResolveMatAsset
    from convert.formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
    from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
    from convert.adapters.Fusion.Native.Graph.ReadNames import ReadNames
    names = {schema.Value.ClassGuid.upper(): schema.NameValue.rsplit('::', 1)[-1] for schema in ReadNames()}
    managers = BindMaterials(model)
    found = []
    for segment in model.Segments:
        if segment.Metadata.Header.SegmentId != 0:
            continue
        for record in segment.Records:
            for group in record.Groups:
                holder = names.get(group.ClassGuid.upper(), group.ClassGuid[:8])
                for field in group.Fields:
                    if field.FieldName not in ('physicalMaterial', 'visualMaterial', 'defaultPhysicalMaterial', 'defaultVisualMaterial'):
                        continue
                    value = field.Value
                    if isinstance(value, OptionalValue):
                        value = value.Value
                    if not isinstance(value, ValueObject):
                        found.append((holder, field.FieldName, 'none', None))
                        continue
                    fields = GroupFields(value.Groups)
                    identity = fields.get('assetReference')
                    reference = fields.get('ProteinAssetManager')
                    if not identity:
                        found.append((holder, field.FieldName, 'empty', None))
                        continue
                    package = managers.get(getattr(reference, 'ObjectId', None))
                    asset = None if package is None else ResolveMatAsset(package, identity)
                    found.append((holder, field.FieldName, 'asset' if asset else 'missing', None if asset is None else (id(package), asset.InstanceId)))
    return found


def census(name, data):
    from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
    try:
        model = ReadDocument(data)
    except Exception:
        return None
    physical = [sum(1 for asset in part.Package.Assets if asset.SchemaName == 'PhysMatSchema') for part in model.Materials]
    try:
        found = references(model)
    except Exception as error:
        return {'name': name, 'error': str(error)[:80]}
    holders = collections.Counter((root, field, kind) for root, field, kind, _ in found)
    bodies = {target for root, field, kind, target in found if root == 'Body' and field == 'physicalMaterial' and target}
    defaults = {target for root, field, kind, target in found if field == 'defaultPhysicalMaterial' and target}
    components = {target for root, field, kind, target in found if root != 'Body' and field == 'physicalMaterial' and target}
    return {
        'name': name,
        'bodies': len(model.Bodies),
        'parts': len(model.Materials),
        'physical': physical,
        'holders': {' '.join(key): value for key, value in holders.items()},
        'body_assets': len(bodies),
        'other_assets': len(components),
        'other_in_bodies': len(components & bodies),
        'all_assets': len(bodies | components),
        'defaults': len(defaults),
        'default_in_all': len(defaults & (bodies | components)),
        'default_records': sum(1 for root, field, kind, target in found if field == 'defaultPhysicalMaterial'),
    }


def job(name):
    from SweepOne import ROOT as base
    data = (base / name).read_bytes()
    if name.endswith('.f3z'):
        from convert.formats.Fusion.BundleCodec.ReadBundle import ReadBundle
        rows = []
        for index, entry in enumerate(ReadBundle(data).Documents):
            if entry.FileName.lower().endswith('.f3d'):
                rows.append(census(f'{name}#{index}', entry.DataValue))
        return rows
    return [census(name, data)]


def main():
    from Sweep import tracked
    names = [name for name in tracked() if name.endswith(('.f3d', '.f3z'))]
    rows = []
    with ProcessPoolExecutor(8) as pool:
        for result in pool.map(job, names, chunksize=8):
            rows.extend(row for row in result if row)
    (BASE / 'MaterialCensus.json').write_text(json.dumps(rows, indent=0))
    shapes = collections.Counter()
    holders = collections.Counter()
    for row in rows:
        if 'error' in row:
            shapes[('error', row['error'])] += 1
            continue
        shapes[(row['bodies'] > 0, row['parts'], tuple(row['physical']), row['all_assets'], row['defaults'], row['default_in_all'], row['default_records'])] += 1
        for key, value in row['holders'].items():
            holders[key] += 1
    for key, value in shapes.most_common(30):
        print(value, json.dumps(key))
    for key, value in holders.most_common(20):
        print(value, key)


if __name__ == '__main__':
    main()
