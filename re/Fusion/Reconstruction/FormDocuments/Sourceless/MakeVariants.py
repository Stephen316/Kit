"""Research probe: one-field variants between a Kit Form document and its native control.

Fusion lost the converted body of source-free Kit Form documents on
`computeAll` and opened closed Kit bodies as sheets. This script edits single
Design fields of the Kit box document toward the native box, and of the native
box toward Kit, so one Fusion run can show which field causes each defect.

The recorded variants were built from the Kit box as emitted at commit
ebdb1dd0b, before fix 12ead0f54. `Variants/KitBase.f3d` keeps those records.
PrepareBuilt.py has since rewritten `Sourceless/Box.f3d` with the fix, so a
rerun of this script produces different Kit variants.
"""

import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed  # noqa: E402
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument  # noqa: E402
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries  # noqa: E402

OUT = ROOT / 're/Fusion/LocalOracle/FormDocuments/Sourceless/Variants'
NAMES = {}
for path in (ROOT / 'src/convert/formats/Fusion').rglob('*Classes.json'):
    for entry in json.loads(path.read_text()):
        NAMES[entry['ClassGuid'].upper()] = entry['NameValue']


def class_of(record):
    return NAMES.get(record.Groups[0].ClassGuid.upper(), '') if record.Groups else ''


def body_ids(model):
    return {r.ObjectId for r in model.Segments[0].Records if r.IsPrimary and class_of(r) == 'Body'}


def fields_of(model, name, test=None):
    found = {}
    for record in model.Segments[0].Records:
        if record.IsPrimary and class_of(record) == name:
            values = {f.FieldName: f.Value for g in record.Groups for f in g.Fields}
            if test is None or test(values):
                found[record.ObjectId] = values
    return found


def edit(model, name, changes, test=None):
    """Replace named fields in every primary record of one class."""
    targets = set(fields_of(model, name, test))
    if not targets:
        raise ValueError(f'no {name} record')
    records = []
    for record in model.Segments[0].Records:
        if record.ObjectId in targets and record.IsPrimary:
            groups = tuple(
                replace(group, Fields=tuple(replace(f, Value=changes[f.FieldName]) if f.FieldName in changes else f for f in group.Fields))
                for group in record.Groups
            )
            record = replace(record, Groups=groups)
        records.append(record)
    segments = (replace(model.Segments[0], Records=tuple(records)), *model.Segments[1:])
    return replace(model, Segments=segments)


def body_generator(values):
    return values.get('rBodies') is not None


def top_generator(values):
    return values.get('rBodies') is None


def native_values(native):
    (body,) = fields_of(native, 'Body').values()
    (generator,) = fields_of(native, 'PassiveIdGenerator', body_generator).values()
    return body, generator


def variants(kit, native):
    body, generator = native_values(native)
    solid = {'bodyType': 2}
    cache = {'cache': body['cache'], 'facetVersion': body['facetVersion']}
    ids = {name: generator[name] for name in ('nextId', 'scanOrderIndex', 'addressOfTopEntities')}
    (kit_body,) = fields_of(kit, 'Body').values()
    blank = {'cache': kit_body['cache'], 'facetVersion': 0}
    empty_ids = {'nextId': 0, 'scanOrderIndex': ValueSeries(()), 'addressOfTopEntities': ValueSeries(())}
    yield 'KitBase', kit
    yield 'KitSolid', edit(kit, 'Body', solid)
    yield 'KitSolidCache', edit(kit, 'Body', {**solid, **cache})
    yield 'KitSolidIds', edit(edit(kit, 'Body', solid), 'PassiveIdGenerator', ids, body_generator)
    yield 'KitSolidCacheIds', edit(edit(kit, 'Body', {**solid, **cache}), 'PassiveIdGenerator', ids, body_generator)
    yield 'NativeBase', native
    yield 'NativeBlankCache', edit(native, 'Body', blank)
    yield 'NativeBlankIds', edit(native, 'PassiveIdGenerator', empty_ids, body_generator)
    yield 'NativeSheet', edit(native, 'Body', {'bodyType': 4})
    (top,) = fields_of(native, 'PassiveIdGenerator', top_generator).values()
    cached = {'nextId': 1, 'scanOrderIndex': ValueSeries((0,)), 'addressOfTopEntities': top['addressOfTopEntities']}
    zero = {**cached, 'addressOfTopEntities': ValueSeries((0,))}
    yield 'KitSolidTop', edit(edit(kit, 'Body', solid), 'PassiveIdGenerator', cached, top_generator)
    yield 'KitSolidTopZero', edit(edit(kit, 'Body', solid), 'PassiveIdGenerator', zero, top_generator)
    yield 'NativeBlankTop', edit(native, 'PassiveIdGenerator', empty_ids, top_generator)


def main():
    OUT.mkdir(exist_ok=True)
    kit = ReadDocument((ROOT / 're/Fusion/LocalOracle/FormDocuments/Sourceless/Box.f3d').read_bytes())
    native = ReadDocument((ROOT / 're/Fusion/LocalOracle/TSpline/Box.f3d').read_bytes())
    rows = []
    for name, model in variants(kit, native):
        payload = EmitParsed(model)
        back = ReadDocument(payload)
        if [s.Records for s in back.Segments] != [s.Records for s in model.Segments] or back.Bodies != model.Bodies:
            raise ValueError(f'{name} does not keep its records')
        (OUT / f'{name}.f3d').write_bytes(payload)
        rows.append({'case': name, 'document_file': f're/Fusion/LocalOracle/FormDocuments/Sourceless/Variants/{name}.f3d', 'document_sha256': hashlib.sha256(payload).hexdigest()})
    (OUT / 'Variants.json').write_text(json.dumps({'scope': 'One-field Design variants between the Kit box and the native box', 'rows': rows}, indent=1) + '\n')
    print(json.dumps(rows, indent=1))


if __name__ == '__main__':
    main()
