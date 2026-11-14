"""Graft other values into the sheet default fields that have no known meaning.

SheetDefaultReasons.json lists 26 rows whose fields keep one value in every drawing Kit has read, but whose meaning
is unknown. This round asks Fusion whether each value can change. The base is D0Plain, the T16 base, which holds
every class involved except an aligned dimension. Only object records change; the header stays untouched.

* Y0Base re-emits D0Plain through the same path as the control of the round.
* Y1Zeros writes 0 into each non-zero unknown field: the inventor subentity manager flag and word, the three
  reference data words, and bit 3 of the dimension flags.
* Y2Raised writes 1 into each zero unknown field: the geometry dependency word and bit, the inventor manager raw
  word, the four hatch manager words, the three reference data bits, the dimension bit, the MTEXT bit and the
  drawing view real. The fifth reference data text becomes "x".
* Y3Manager, Y4Reference and Y5DimBit split Y1Zeros by class: the inventor manager pair, the three reference data
  words, and bit 3 of the dimension flags.
* Z1Flag to Z6Three write 0 into one field each of the two classes that Fusion reports as damaged. Z3Long65 and
  Z7One3 write another non-zero value, which tells an exact value from any non-zero one.
* Z8Long1, Z9One1, ZaTwo2 and ZbThree2 try the smallest other non-zero value of each word Fusion needs.
* R1Geom to R7ViewReal split Y2Raised by class, because Fusion stops answering while it opens Y2Raised.
* MLong2 to MLong1000 bracket the smallest inventor manager word Fusion accepts, between 1 (damaged) and 64.
* HTwo to HFive and FFlagOne to FTextFive change one field each of the two classes whose Y2Raised split failed.

The plan goes to Variants/PlanUnknowns.json, and each variant to Variants/<label>.f3z.
Run: python3.14 -I BuildUnknowns.py --bundle $TMPDIR/KitFusionDrawings/Variants/D0Plain.f3z
"""

import argparse
import io
import json
import sys
import zipfile
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / 'Dwg'))
sys.path.insert(0, str(HERE.parent / 'Authoring'))
sys.path.insert(0, str(HERE.parents[4] / 'src'))

import BuildPruned  # noqa: E402
import BuildPruned2  # noqa: E402
import BuildVariants  # noqa: E402
from PruneDwg import field, with_fields  # noqa: E402

from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile  # noqa: E402

PLAN = 'PlanUnknowns.json'
ZEROS = {
    'ACDBASSOCINVENTORPERSSUBENTIDMANAGER': {'ManagerFlag': 0, 'ManagerLong': 0},
    'ACDBREFERENCEDATA': {'LongOne': 0, 'LongTwo': 0, 'LongThree': 0},
    'DIMENSION_LINEAR': {'DimFlags': lambda value: value & ~8},
}
SPLITS = (('Y3Manager', 'ACDBASSOCINVENTORPERSSUBENTIDMANAGER'), ('Y4Reference', 'ACDBREFERENCEDATA'), ('Y5DimBit', 'DIMENSION_LINEAR'))
MANAGER = 'ACDBASSOCINVENTORPERSSUBENTIDMANAGER'
REFERENCE = 'ACDBREFERENCEDATA'
SINGLES = (
    ('Z1Flag', {MANAGER: {'ManagerFlag': 0}}),
    ('Z2Long', {MANAGER: {'ManagerLong': 0}}),
    ('Z3Long65', {MANAGER: {'ManagerLong': 65}}),
    ('Z4One', {REFERENCE: {'LongOne': 0}}),
    ('Z5Two', {REFERENCE: {'LongTwo': 0}}),
    ('Z6Three', {REFERENCE: {'LongThree': 0}}),
    ('Z7One3', {REFERENCE: {'LongOne': 3}}),
    ('Z8Long1', {MANAGER: {'ManagerLong': 1}}),
    ('Z9One1', {REFERENCE: {'LongOne': 1}}),
    ('ZaTwo2', {REFERENCE: {'LongTwo': 2}}),
    ('ZbThree2', {REFERENCE: {'LongThree': 2}}),
)
BRACKET = tuple(('MLong' + str(value), {MANAGER: {'ManagerLong': value}}) for value in (2, 8, 16, 32, 48, 63, 1000, 66, 96, 127, 128, 192, 256))
HATCH = 'ACDBASSOCVIEWREPHATCHMANAGER'
PARTS = tuple(('H' + name[11:], {HATCH: {name: 1}}) for name in ('ManagerLongTwo', 'ManagerLongThree', 'ManagerLongFour', 'ManagerLongFive')) + tuple(
    ('F' + name, {REFERENCE: {name: value}}) for name, value in (('FlagOne', 1), ('FlagTwo', 1), ('FlagThree', 1), ('TextFive', 'x')))
RAISES = (
    ('R1Geom', 'ACDBASSOCGEOMDEPENDENCY'),
    ('R2Raw', MANAGER),
    ('R3Hatch', 'ACDBASSOCVIEWREPHATCHMANAGER'),
    ('R4RefFlags', REFERENCE),
    ('R5DimUnknown', 'DIMENSION_LINEAR'),
    ('R6Mtext', 'MTEXT'),
    ('R7ViewReal', 'DRAWINGVIEW'),
)
RAISED = {
    'ACDBASSOCGEOMDEPENDENCY': {'GeomLongFour': 1, 'GeomFlag': 1},
    'ACDBASSOCINVENTORPERSSUBENTIDMANAGER': {'ManagerRaw': 1},
    'ACDBASSOCVIEWREPHATCHMANAGER': {'ManagerLongTwo': 1, 'ManagerLongThree': 1, 'ManagerLongFour': 1, 'ManagerLongFive': 1},
    'ACDBREFERENCEDATA': {'FlagOne': 1, 'FlagTwo': 1, 'FlagThree': 1, 'TextFive': 'x'},
    'DIMENSION_LINEAR': {'Unknown': 1},
    'MTEXT': {'UnknownBit': 1},
    'DRAWINGVIEW': {'RealSix': 1.0},
}


def bundle_parts(path):
    archive = zipfile.ZipFile(io.BytesIO(Path(path).read_bytes()))
    drawing = next(archive.read(name) for name in archive.namelist() if name.endswith('.f2d'))
    source = next(archive.read(name) for name in archive.namelist() if name.endswith('.f3d'))
    return drawing, source


def typed(old, new):
    if isinstance(old, bool):
        return bool(new)
    if isinstance(old, float):
        return float(new)
    return new


def changed(dwg, plan):
    objects, edits = [], []
    for obj in dwg.DwgObjects:
        wanted = plan.get(obj.ClassKind)
        if not wanted:
            objects.append(obj)
            continue
        common, data = obj.CommonData, obj.ClassData
        for name, value in wanted.items():
            for part, record in (('Common', common), ('Data', data)):
                old = field(record, name, KeyError)
                if old is KeyError:
                    continue
                new = typed(old, value(old) if callable(value) else value)
                record = with_fields(record, **{name: new})
                edits.append({'class': obj.ClassKind, 'handle': obj.ObjectHandle, 'part': part, 'field': name, 'old': old, 'new': new})
                if part == 'Common':
                    common = record
                else:
                    data = record
                break
            else:
                raise ValueError(f'{obj.ClassKind} has no field {name}')
        objects.append(replace(obj, CommonData=common, ClassData=data))
    return replace(dwg, DwgObjects=tuple(objects)), edits


def check(data, edits):
    again = ReadDwgFile(data)
    by_handle = {obj.ObjectHandle: obj for obj in again.DwgObjects}
    for edit in edits:
        obj = by_handle[edit['handle']]
        record = obj.CommonData if edit['part'] == 'Common' else obj.ClassData
        if field(record, edit['field']) != edit['new']:
            raise ValueError(f'{edit} did not read back')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', required=True)
    args = parser.parse_args()
    out = BuildVariants.OUT
    drawing, source = bundle_parts(args.bundle)
    base = ReadDwgFile(BuildVariants.database(drawing))
    plan = {'base': Path(args.bundle).name, 'base_objects': len(base.DwgObjects), 'variants': []}
    rounds = [('Y0Base', {}), ('Y1Zeros', ZEROS), ('Y2Raised', RAISED)]
    rounds += [(label, {name: ZEROS[name]}) for label, name in SPLITS]
    rounds += list(SINGLES)
    rounds += [(label, {name: RAISED[name]}) for label, name in RAISES]
    rounds += list(BRACKET)
    rounds += list(PARTS)
    for label, edits_plan in rounds:
        dwg, edits = changed(base, edits_plan)
        data = BuildPruned.emit_fresh(dwg)
        check(data, edits)
        bundle = BuildVariants.opaque_bundle(BuildVariants.without_database(drawing, data), source, label)
        row = BuildPruned2.record(out, label, bundle, data, dwg, {})
        row['edits'] = edits
        plan['variants'].append(row)
    (out / PLAN).write_text(json.dumps(plan, indent=1, default=str) + '\n')
    print(json.dumps([(row['label'], row['objects'], row['dwg_bytes'], len(row['edits'])) for row in plan['variants']]))


if __name__ == '__main__':
    main()
